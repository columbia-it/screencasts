import time
import boto3
import requests
import argparse
import uuid
import json

class Timestamp:
    def __init__(self, sec):
        self._sec = float(sec)

    @property
    def hours(self):
        return int(self._sec // 3600)

    @property
    def minutes(self):
        minutes = self._sec % 3600
        return int(minutes // 60)

    @property
    def seconds(self):
        remainder = self._sec % 3600
        return round(remainder % 60, 3)

    def __sub__(self, other):
        return Timestamp(self._sec - other._sec)

    def __add__(self, other):
        return Timestamp(self._sec + other._sec)

    def __gt__(self, other):
        return self._sec > other._sec

    def __str__(self):
        return '{:02d}:{:02d}:{:06.3f}'.format(self.hours, self.minutes, self.seconds)

    def srt(self):
        """ .srt file format for timestamp """
        return '{:02d}:{:02d}:{:02d},{:03d}'.format(self.hours, self.minutes,
                                                    int(self.seconds // 1),
                                                    int(self.seconds % 1 * 100))

class Word:
    """
    Represent an utterance
    See  https://www.w3.org/TR/webvtt1/#webvtt-timestamp
    """
    def __init__(self, start_time, end_time, word, type):
        self.start = Timestamp(start_time)
        self.end = Timestamp(end_time)
        self.word = word
        self.type = type

    def __str__(self):
        return '{} --> {}\n{}\n'.format(self.start, self.end, self.word)

    def srt(self):
        """ .srt file format instead """
        return '{} --> {}\n{}\n'.format(self.start.srt(), self.end.srt(), self.word)

    def __add__(self, other):
        """concatenate the words together, extending the end time"""
        space = '' if other.type == 'punctuation' else ' '
        new = Word('0.0', '0.0', self.word + space + other.word, self.type)
        new.start = self.start
        new.end = other.end
        return new

class Session:
    def __init__(self, profile_name=None, vocab=None):
        self.session = boto3.session.Session(profile_name=profile_name)
        self.vocab = vocab

    def set_vocab(self, vocab):
        self.vocab = vocab

    def copy_s3(self, infile, bucket):
        s3 = self.session.client('s3')
        file = infile[infile.rfind('/')+1:]
        response = s3.put_object(Body=open(infile, 'rb'), Bucket=bucket, Key=file)
        return 's3://' + bucket + '/' + file

    def delete_s3(self, s3url):
        s3 = self.session.client('s3')
        bucket = s3url[len('s3://'):s3url.rfind('/')]
        file = s3url[s3url.rfind('/')+1:]
        s3.delete_object(Bucket=bucket, Key=file)

    def start_job(self, s3url):
        # https://docs.aws.amazon.com/transcribe/latest/dg/how-vocabulary.html
        job_uri = s3url
        job_name = job_uri.replace('s3://', '').replace('/', '-')
        job_name = job_name[:job_name.find('.')] + '-' + str(uuid.uuid4())
        transcribe = self.session.client('transcribe')
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat=s3url[s3url.rfind('.')+1"] -- allow .mp3, .mp4 and so on
            LanguageCode='en-US',
            Settings={
                'VocabularyName': self.vocab,
            },
        )
        print('Job {} submitted'.format(job_name))
        return job_name

    def wait_job(self, job_name):
        transcribe = self.session.client('transcribe')
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            print("job {} not ready yet...".format(job_name))
            time.sleep(10)
        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            result = requests.get(uri).json()
            json.dump(result, open(job_name + '.json', 'w'), indent=2)
            return result
        else:
            print("failed.")
            return None

    def use_saved(self, job_name):
        return json.load(open(job_name + '.json', 'r'))

    def delete_job(self, job_name):
        transcribe = self.session.client('transcribe')
        transcribe.delete_transcription_job(
            TranscriptionJobName=job_name
        )

PROFILE = 'alan:CTO'

def main(args=None):
    parser = argparse.ArgumentParser(usage='%(prog)s [options] infile outfile')
    parser.add_argument('infile',
                        help='local file or s3 url')
    parser.add_argument('outfile',
                        help='output VTT file')
    parser.add_argument('--srt',
                        help='output SRT file')
    parser.add_argument('--profile', default=PROFILE,
                        help='AWS config profile [default %(default)s]')
    parser.add_argument('--job', default=None,
                        help='existing AWS transcribe job')
    parser.add_argument('--saved_job', default=None,
                        help='use saved AWS transcribe job output')
    parser.add_argument('--job_delete', action='store_true', default=False,
                        help='delete transcription job',
                        )
    parser.add_argument('--vocabulary', default='jsonapi',
                        help='custom vocabulary to use [default: %(default)s]')
    parser.add_argument('--s3bucket', default='n2ygk',
                        help='s3 bucket [default: %(default)s]')
    parser.add_argument('--s3_delete', action='store_true', default=False,
                        help='delete s3 file',
                        )

    opt = parser.parse_args(args)
    outfile = open(opt.outfile, 'x')
    srtfile = open(opt.srt, 'x') if opt.srt else None
    session = Session(profile_name=opt.profile, vocab=opt.vocabulary)
    s3url = opt.infile if opt.infile.startswith('s3:') else session.copy_s3(opt.infile, opt.s3bucket)
    if opt.saved_job:
        response = session.use_saved(opt.saved_job)
    else:
        job_name = opt.job if opt.job else session.start_job(s3url)
        response = session.wait_job(job_name)

    words = []
    prev_start = prev_end = '0.0'
    for item in response['results']['items']:
        s = prev_start if item['type'] == 'punctuation' else item['start_time']
        e = prev_end if item['type'] == 'punctuation' else item['end_time']
        words.append(Word(s, e, item['alternatives'][0]['content'], item['type']))
        prev_start = s
        prev_end = e
    phrases = []
    nwords = len(words)
    minwords = 3
    maxwords = 9
    maxtime = Timestamp(1.0)
    curw = words[0]
    curi = 1
    for i in range(1, nwords):
        nextw = words[i]
        interword_time = nextw.start - curw.end
        if (curi > maxwords) or (interword_time > maxtime) or (curi > minwords and curw.word[-1] in '.,;!'):
            curw.end += interword_time
            phrases.append(curw)
            curw = nextw
            curi = 1
        else:
            curw += nextw
            curi += 1

    phrases.append(curw)

    print("WEBVTT\n", file=outfile)
    if srtfile:
        print("", file=srtfile)
    for i, w in enumerate(phrases):
        print(i+1, file=outfile)
        print(w, file=outfile)
        if srtfile:
            print(i+1, file=srtfile)
            print(w.srt(), file=srtfile)
            
    if opt.job_delete:
        session.delete_job(job_name)
    if opt.s3_delete:
        session.delete_s3(s3url)

if __name__ == '__main__':
    main()

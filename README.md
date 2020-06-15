# Making Screencasts on MacOS

<!-- generate a ToC with "markdown-toc -i README.md" -->

<!-- toc -->

- [Record with QuickTime](#record-with-quicktime)
  * [Make sure the resolution is just enough](#make-sure-the-resolution-is-just-enough)
  * [Trim and/or Edit](#trim-andor-edit)
  * [Convert to MP4](#convert-to-mp4)
- [Record with Zoom](#record-with-zoom)
- [Split the MP4 video](#split-the-mp4-video)
- [Add captions using AWS transcribe service](#add-captions-using-aws-transcribe-service)
- [Improve automated transcription with custom vocabulary](#improve-automated-transcription-with-custom-vocabulary)
- [Manually review and fix the transcription](#manually-review-and-fix-the-transcription)
- [Generate a transcript with video references](#generate-a-transcript-with-video-references)
- [Wrap in HTML with some Javascript controls](#wrap-in-html-with-some-javascript-controls)
- [Batching it all up](#batching-it-all-up)
- [Review locally before deploying](#review-locally-before-deploying)
- [Deploy to a web server](#deploy-to-a-web-server)
- [Deploy to Google Docs](#deploy-to-google-docs)
- [Browser Compatibility](#browser-compatibility)

<!-- tocstop -->

## Record with QuickTime

Use [Command-Shift-5](https://support.apple.com/en-us/HT208721) and make a Quicktime recording.

For an alternative, see [Record with Zoom](#record-with-zoom), below.

### Make sure the resolution is just enough

Note that recording the Retina display makes a giant resolution file. Find a way to reduce it to something reasonable.

Here are some speed comparisons:

ffmpeg conversion of a 5:54 long fullscreen recording (3360 x 2114 resolution, 60 fps):
```
frame=  432 fps= 60 q=31.0 size=    1042kB time=00:00:07.12 bitrate=1198.7kbits/s speed=0.993x
```

The same video after downscaling the Quicktime and reducing the frame rate from 60 to 15 fps with ffmpeg
(Quicktime Export as 720p; 1152 x 738 resolution, 15 fps):
```
frame= 1525 fps=252 q=27.0 size=    5888kB time=00:01:42.57 bitrate= 470.3kbits/s dup=0 drop=4355 speed=  17x
```

Using ffmpeg to downscale the QuickTime works OK too (and can be batched). It runs at about 2.5x.

```
ffmpeg -i resolution.mov -vcodec h264 -acodec mp2 -r 15 -vf "scale=qhd" resolution-scaled-qhd.mp4
```

Some size comparisons of various scaled resolutions:

```
(env) screencast$ ls -l 02/01jsonapi*.mp4
-rw-r--r--  1 ac45  1749373939  43916456 Jul  6 14:44 02/01jsonapi-15fps.mp4
-rw-r--r--@ 1 ac45  1749373939  24769616 Jul  6 14:16 02/01jsonapi-720-15fps.mp4
-rw-r--r--@ 1 ac45  1749373939  32668772 Jul  6 14:13 02/01jsonapi-720.mp4
-rw-r--r--@ 1 ac45  1749373939  21752453 Jul  6 14:51 02/01jsonapi-scaled-840-528.mp4
-rw-r--r--  1 ac45  1749373939  21492952 Jul  6 15:05 02/01jsonapi-scaled-hd480.mp4
-rw-r--r--@ 1 ac45  1749373939  25663549 Jul  6 14:58 02/01jsonapi-scaled-hd720.mp4
-rw-r--r--  1 ac45  1749373939  22618104 Jul  6 15:08 02/01jsonapi-scaled-qhd.mp4
-rw-r--r--  1 ac45  1749373939  73275598 Jul  6 11:47 02/01jsonapi.mp4
```

### Trim and/or Edit

Within the screen recording you can trim off the beginning and end. Use iMovie or something else to edit further.

### Convert to MP4

Next, convert the MOV video to MP4 so it can be viewed in a browser.
You can use [ffmpeg](https://ffmpeg.org/ffmpeg.html) for this.

```
$ brew install ffmpeg
$ ffmpeg -i test.mov -vcodec h264 -acodec mp2 -r 15 test.mp4
```

## Record with Zoom

A perhaps better alternative to recording with QuickTime, although one that comes at a cost, is to record a Zoom
meeting with yourself.  Unlike with QuickTime recordings that can only record the full screeen or a portion of it,
Zoom can record the full screen or a specific application window.  When recording, select Record on this Computer.
At the end of the meeting, the recording will be delivered as an MP4 so you don't have to transcode with with ffmpeg.

## Split the MP4 video

The Zoom session may contain multiple topics. You can split the zoom_0.mp4 into multiple files
with tools like avidemux:

```
$ brew cask install avidemux
```

In Finder, go to Applications and open Avidemux, then:

1. File/Open zoom_0.mp4
2. Click on "A" to set the start point of the clip.
3. Scroll forward to the end and click on "B".
4. Select "MP4 Muxer" as the Output Format.
5. Select "Save" and give it a name (e.g. zoom_1.mp4).


## Add captions using AWS transcribe service

Create a [WEBVTT](https://www.w3.org/TR/webvtt1/) file and just add the text track `<track>`.

See [aws-transcribe.py](aws-transcribe.py) which does a few things:
```text
usage: aws-transcribe.py [options] infile outfile

positional arguments:
  infile                local file or s3 url
  outfile               output VTT file

optional arguments:
  -h, --help            show this help message and exit
  --srt SRT             output SRT file
  --profile PROFILE     AWS config profile [default alan:CTO]
  --job JOB             existing AWS transcribe job
  --saved_job SAVED_JOB
                        use saved AWS transcribe job output
  --job_delete          delete transcription job
  --vocabulary VOCABULARY
                        custom vocabulary to use [default: jsonapi]
  --s3bucket S3BUCKET   s3 bucket [default: n2ygk]
  --s3_delete           delete s3 file
```

- Copies the .mp4 file to S3. If the file is already there, provide an s3:// URL that references it.
- Submits a transcribe job. If the job has already been submitted, provide the `--job` option.
- Waits for the job to complete.
- Pulls the transcription data from AWS.
- Merges the individual words and punctionation into phrases.
- Outputs a .VTT file.
- Deletes the transcripion job results unless `--no_delete` option is used.

## Improve automated transcription with custom vocabulary

The transcription will likely have some systemic errors for things like jargon, specific acronynms and so on.
You can upload a [custom vocabulary](https://docs.aws.amazon.com/transcribe/latest/dg/how-vocabulary.html) to
AWS and apply it to the transcription.

```text
(env) screencast$ aws s3 cp jsonapi-vocab.txt s3://n2ygk --profile alan:CTO
(env) screencast$ aws transcribe create-vocabulary --vocabulary-name jsonapi --language-code en-US --vocabulary-file-uri s3://n2ygk/jsonapi-vocab.txt --profile alan:CTO
{
    "VocabularyName": "jsonapi",
    "LanguageCode": "en-US",
    "VocabularyState": "PENDING"
}
...
(env) screencast$ aws transcribe list-vocabularies --profile alan:CTO
{
    "Vocabularies": [
        {
            "VocabularyName": "jsonapi",
            "LanguageCode": "en-US",
            "VocabularyState": "READY"
        }
    ]
}	
```

Here's an example of some vocabulary improvments:
```diff
4,5c4,5
< 00:00:00.700 --> 00:00:04.970
< This is an introduction at rest ful ap eyes rests
---
> 00:00:00.700 --> 00:00:05.670
> This is an introduction at RESTful APIs rests APIs air
8,9c8,9
< 00:00:04.970 --> 00:00:07.870
< AP Eyes were frequently used for micro service is and
---
> 00:00:05.670 --> 00:00:07.510
> frequently used for microservices.
12,13c12,13
< 00:00:07.870 --> 00:00:10.140
< we'll talk a little bit more about that as we ...
---
291,297c283,285
< 73
< 00:03:43.980 --> 00:03:44.570
< hate. Oh,
< 
< 74
< 00:03:44.570 --> 00:03:45.790
< yes, kind of thing,
---
> 71
> 00:03:43.980 --> 00:03:45.790
> HATEOAS kind of thing,
```

## Manually review and fix the transcription

The transcription will have some errors. Edit the `.vtt` file to fix them.
`aws-transcribe` will not overwrite an existing .vtt file.

Some further manual improvements:
```diff
240,241c240,241
< 00:03:12.070 --> 00:03:15.300
< which will get into later called JSON API I dot
---
> 00:03:12.070 --> 00:03:15.580
> -- which we will get into later -- called JSONAPI.org

```
## Generate a transcript with video references

[vtt2transcript.py](vtt2transcript.py) reads the (corrected) `.vtt` file and generates a hyperlinked
transcript where each phrase from the captioning causes the video to jump to the associated time.

## Wrap in HTML with some Javascript controls

Here's an example:
```html
<!DOCTYPE html> 
<html> 
<head>
<link rel="stylesheet" type="text/css" href="transcript.css">
<script type = "text/javascript" src="videocontrols.js"></script>

<title>s3test</title>
</head>
<body>

<div style="text-align:center"> 

  <button onclick="makeSmall()">Small</button>
  <button onclick="makeBig()">Big</button>
  <br><br>
  <video id="video1" width="50%" controls preload="metadata">
    <source src="s3test.mp4" type="video/mp4">
    <track label="English" kind="captions" srclang="en" src="s3test.vtt" default>
    Your browser does not support HTML5 video.
  </video>
  <br>
  <button onclick="slowerSpeed()">Slow down</button>
  <button onclick="normalSpeed()">Speed 1.0</button>
  <button onclick="fasterSpeed()">Speed up</button>
  <button onclick="captionsOn()">Captions ON</button>
  <button onclick="captionsOff()">Captions Off</button>
</div> 

<script>
setVideo("video1");
</script>


<p>Transcript</p>

<div w3-include-html="s3test-transcript.html"></div>
<script>includeHTML()</script>
</body> 
</html>
```

## Batching it all up

See [batchtranscribe.sh](batchtranscribe.sh) and [batchvtt2transcript.sh](batchvtt2transcript.sh) which
convert and transcribe the Quicktime videos, and then, after cleaning up the VTT transcripts, generates
hyperlinked transcripts.

## Review locally before deploying

NOTE: That when you try to test locally by just opening the file, the subtitles
[will not work in Chrome](https://stackoverflow.com/questions/3828898/can-chrome-be-made-to-perform-an-xsl-transform-on-a-local-file)
but will work in other browsers like Firefox. However, the transcript file refuses to display.

So, run a simple http server locally:
```text
(env) screencast$ npm install http-server -g
/usr/local/bin/http-server -> /usr/local/lib/node_modules/http-server/bin/http-server
/usr/local/bin/hs -> /usr/local/lib/node_modules/http-server/bin/http-server
+ http-server@0.11.1
added 3 packages from 6 contributors and updated 10 packages in 0.905s
(env) screencast$ http-server 
Starting up http-server, serving ./
Available on:
  http://127.0.0.1:8080
  http://160.39.178.127:8080
Hit CTRL-C to stop the server
```

## Deploy to a web server

Just copy the files to a web server:
```
(env) screencast$ scp videocontrols.js 02/01jsonapi.mp4 02/01jsonapi.vtt 02/01jsonapi.html 02/01jsonapi-transcript.html alan@cunix:public_html/
(env) screencast$ ssh alan@cunix chmod a+r public_html/01*
```

## Deploy to Google Docs

Google Docs magically handles MP4 files and you can even add captions:
1. Google only supports SRT transcript files. `aws-transcribe` has a `--srt FILE` option to generate
this at the same time as the VTT is generated.
1. Upload the MP4 video file to google docs.
1. Click on it after waiting a while -- it will tell you it's still processing it.
1. Click on the vertical `. . .` menu and select "manage caption tracks" and upload your SRT file.

## Browser Compatibility

TODO: So far this only works fully with Chrome. 

Firefox: Fails to render the transcript text.

Safari: Fails to play sound.



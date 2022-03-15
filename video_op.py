import moviepy.editor as mp
import speech_recognition as sr 
import os 
import language_tool_python
import pandas as pd
import boto3
import requests
import json
import time
import datetime

cwd = os.getcwd()

def video2audio(filename, path):
    print("Converting video to audio..")
    my_clip = mp.VideoFileClip(path)
    video_duration = int(my_clip.duration)
    if video_duration > 120:
        return "INSERT_SMALLER_CLIP"
    ## Other opertaions
    audio_ = str(filename.split(".")[0]) + ".wav"
    write_path = os.path.join("static", "results", audio_)
    print(write_path)
    my_clip.audio.write_audiofile(write_path)
    return write_path

def audio_to_text(path, file_name):
    print("Converting audio to text..")

    client=boto3.client("transcribe", region_name="us-east-2",aws_access_key_id="KEY", 
                    aws_secret_access_key="KEY")

    filename = "audio3.wav"
    media_uri = 's3://speechtotextbkt/' + filename
    trans_name = 'transcrib_job_one'
    response = client.start_transcription_job(
        TranscriptionJobName= trans_name,
        LanguageCode='en-IN',
        MediaSampleRateHertz=48000,
        MediaFormat='wav',
        Media={'MediaFileUri': media_uri},
        OutputBucketName='speechtotextbkt'
    )
    
    status_response = client.get_transcription_job(
        TranscriptionJobName='transcrib_job_one'
    )
    items_df = None
    transcripts = None
    while True:
        time.sleep(5)
        status_response = client.get_transcription_job(
            TranscriptionJobName='transcrib_job_one'
            )
        status = status_response["TranscriptionJob"]["TranscriptionJobStatus"]
        print(status)
        if status == "COMPLETED":
            uri = status_response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            trans = requests.get(uri)
            
            s3 = boto3.client('s3',region_name="us-east-2",aws_access_key_id="KEY", 
                    aws_secret_access_key="KEY")
            s3.download_file('speechtotextbkt', 'transcrib_job_one.json', 'result.json')
            with open("result.json", "rb") as f:
                content = json.load(f)

            items = content["results"]["items"]
            items_df = pd.DataFrame(items, columns = items[0].keys())
            items_df["content"] = items_df["alternatives"].apply(lambda x: x[0]["content"])
            items_df["confidence"] = items_df["alternatives"].apply(lambda x: x[0]["confidence"])
            items_df = items_df.drop(["alternatives"], axis=1)
            
            transcripts = content["results"]["transcripts"][0]["transcript"]
            break
    '''r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio_listened = r.record(source)
        # try converting it to text
        try:
            text = r.recognize_google(audio_listened,language='en-US')
        except sr.UnknownValueError as e:
            print("Error:", str(e))
            return "NO_AUDIO_FOUND"
        else:
            text = f"{text.capitalize()}. "
            text_file_name = str(file_name.split('.')[0]) + ".txt"
            txt_path = os.path.join(cwd, "static", "transcripts", "OG", text_file_name)
            with open(txt_path, "w") as fp:
                fp.write(text)
            return text'''
    return transcripts, items_df


def check_grammer(text):
    print("Checking grammer..")
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    return matches

def tabularization(matches, file_name):
    print("Tabularizing the results...")
    if not len(matches):
        return "NO_MISTAKES_FOUND", "NONE"
    list_a, list_b, list_c, list_d = [], [], [], []
    for i in range(len(matches)):
        list_a.append(matches[i].errorLength)
        list_b.append(matches[i].message)
        list_c.append(matches[i].replacements)
        list_d.append(matches[i].context)

    df=pd.DataFrame({"Error Length":list_a,"Message":list_b,"Replacement":list_c,"Sentence":list_d})
    csv_name = str(file_name.split('.')[0]) + ".csv"
    path = os.path.join(cwd, "static", "transcripts", "changed", csv_name)
    df.to_csv(path)
    return df, path

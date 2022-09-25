import logging
import subprocess
from pprint import pprint
from tempfile import _TemporaryFileWrapper

from ffmpy import FFmpeg

import gradio as gr
from functions import (Clear, CommandBuilder, audio_channels, audio_codecs,
                       audio_quality, audio_sample_rates,
                       change_clipbox, containers, customBitrate, mediaChange, presets, supported_codecs, supported_presets, video_codecs, video_containers,
                       vf)

logging.basicConfig(level=logging.INFO)


logging.info(msg=f"{video_containers}")


def convert(file: _TemporaryFileWrapper, options: str,state):
    stderr=""
    stdout=""
    output_file=""
    video=""
    ffmpeg=FFmpeg()
    try:
        logging.info(f"File name: {file.name}")
        new_name, _ = file.name.split(".")
        logging.info(f"New filename:{new_name}")
        output_file = f"{new_name}1.{options.lower()}"
        ffmpeg = FFmpeg(inputs={file.name: None}, outputs={
                        output_file: ffmpeg_commands.commands.split()}, global_options=["-y", "-hide_banner"])
        print(ffmpeg)
        print(ffmpeg.cmd)

        ffmpeg.run(stderr=subprocess.PIPE)
        # pprint(f"{stdout} {stderr}")
        output=f"{ffmpeg.cmd}"
        # video=gr.update(label=output_file,value=output_file)

    except Exception as e:
        stderr=e
        output=f"{stderr}"
        return [None,None,None,output]

    state=output_file    

    return [output_file,output_file,output_file,output,state]


with gr.Blocks(css="./styles.css") as dm:
    with gr.Tabs():
        with gr.TabItem("Format"):
            # Input Buttons
            with gr.Row():
                with gr.Column() as inputs:
                    file_input = gr.File()
                    options = gr.Radio(
                        label="options", choices=containers,value=containers[0])
                    with gr.Row():
                        with gr.Row() as inputs_clip:
                            clip = gr.Dropdown(
                                choices=["None", "Enabled"], label="Clip:", value="None")
                            start_time = gr.Textbox(
                                label="Start Time:", placeholder="00:00", visible=False,interactive=True)
                            stop_time = gr.Textbox(
                                label="Stop Time:", placeholder="00:00", visible=False)
                    with gr.Row():
                        clearBtn = gr.Button("Clear")
                        convertBtn = gr.Button("Convert", variant="primary")

                # Output Buttons
                with gr.Column():
                    # media_output = gr.Audio(label="Output")
                    with gr.Row():
                        video_button=gr.Button("Video")
                        audio_button=gr.Button("Audio")
                        file_button=gr.Button("File")
                    media_output_audio = gr.Audio(type="filepath",label="Output",visible=True,interactive=False,source="filepath")
                    media_output_video = gr.Video(label="Output",visible=False)
                    media_output_file = gr.File(label="Output",visible=False)
                    with gr.Row() as command_output:
                        output_textbox = gr.Textbox(label="command",elem_id="outputtext")
                
                resetFormat=Clear(inputs,inputs_clip)
                print(inputs_clip.children)
                print(resetFormat)
                state=gr.Variable()
                clearBtn.click(resetFormat.clear, inputs=resetFormat(), outputs=resetFormat())
                convertBtn.click(convert, inputs=[file_input, options,state], outputs=[
                    media_output_audio,media_output_file,media_output_video, output_textbox,state])

        with gr.TabItem("Video"):
            with gr.Row() as video_inputs:
                video_options = gr.Dropdown(
                    label="video", choices=video_codecs,value=video_codecs[-1])
                preset_options = gr.Dropdown(choices=presets, label="presets",value=presets[-1])


            with gr.Row(elem_id="button"):
                with gr.Column():
                    clearBtn = gr.Button("Clear")
            videoReset=Clear(video_inputs)
            clearBtn.click(videoReset.clear, videoReset(), videoReset())

        with gr.TabItem("Audio"):
            with gr.Row() as audio_inputs:
                # print(names[0])
                audio_options = gr.Dropdown(
                    label="audio", choices=audio_codecs, value=audio_codecs[-1])
                audio_bitrate=gr.Dropdown(choices=audio_quality, label="Audio Qualities",
                            value=audio_quality[0])
                custom_bitrate=gr.Number(label="Audio Qualities",visible=False)
                gr.Dropdown(choices=audio_channels,
                            label="Audio Channels", value=audio_channels[0])
                gr.Dropdown(choices=audio_sample_rates,
                            label="Sample Rates", value=audio_sample_rates[0])


            with gr.Column(elem_id="button"):
                clearBtn = gr.Button("Clear")
            audioReset=Clear(audio_inputs)
            clearBtn.click(audioReset.clear, audioReset(), audioReset())

        with gr.TabItem("Filters") as filter_inputs:
            gr.Markdown("## Video")
            with gr.Row().style(equal_height=True) as filter_inputs:
                for i in vf:
                    # print(i.values())
                    # values = list(i.values())
                    values=list(i.values())[0]
                    choices=[j for lst in values for j in [lst.get("name")]]
                    a=gr.Dropdown(label=list(i.keys()),
                                choices=choices, value=choices[0])
            gr.Markdown("## Audio")
            with gr.Row(elem_id="acontrast") as filter_inputs_1:
                acontrastSlider=gr.Slider(label="Acontrast", elem_id="acontrast")

            with gr.Column(elem_id="button"):
                clearBtn = gr.Button("Clear")

            filterReset=Clear(filter_inputs,filter_inputs_1)
            clearBtn.click(filterReset.clear, filterReset(), filterReset())
    
    """ Format Tab change functions"""
    ffmpeg_commands=CommandBuilder(inputs_clip,video_inputs,audio_inputs,filter_inputs,filter_inputs_1)
    # ffmpeg_commands.do()
    dm.load(fn=ffmpeg_commands.reset,inputs=[],outputs=[])
    pprint(ffmpeg_commands.commands)
    ffmpeg_commands.update(output_textbox)
    # file_input.change(fn=updateOutput,inputs=file_input,outputs=output_textbox)
    clip.change(fn=change_clipbox, inputs=clip,
                outputs=[start_time, stop_time])
    
    options.change(supported_codecs,[options],[video_options,audio_options])
    # options.change(mediaChange,[options],[media_output_audio,media_output_video])
    # video_button.click(fn=videoChange,inputs=media_output_file,outputs=media_output_video)
    audio_button.click(mediaChange,[audio_button,state],[media_output_audio,media_output_video,media_output_file])
    video_button.click(mediaChange,[video_button,state],[media_output_audio,media_output_video,media_output_file])
    # media_output_audio.change(lambda x:gr.update(value=x),[media_output_audio],[media_output_video])
    file_button.click(mediaChange,[file_button,state],[media_output_audio,media_output_video,media_output_file])
    """Video Tab change functions"""
    video_options.change(supported_presets,[video_options],[preset_options])
    """Audio Tab change functions"""
    audio_bitrate.change(customBitrate,[audio_bitrate],[custom_bitrate])

if __name__=='__main__':
    dm.launch()

import logging
import os
import subprocess
from tempfile import _TemporaryFileWrapper

from ffmpy import FFmpeg

import gradio as gr

logging.basicConfig(level=logging.INFO)

def convert(file:_TemporaryFileWrapper,options:list,):
	logging.info(f"Current working path :{os.getcwd()}")
	logging.info(f"File name: {file.name}")
	# options.append(["Boy","Girl"])
	new_name,_=file.name.split(".")
	logging.info(f"New filename:{new_name}")
	cm=["ffmpeg","-y","-i",file.name,f"{new_name}.{options}"]
	output_file=f"{new_name}.{options}"	
	ffmpeg=FFmpeg(inputs={file.name:None},outputs={output_file:None},global_options=["-y","-hide_banner"])
	print(ffmpeg)
	ffmpeg.run()
	# subprocess.run(cm,text=True)
	# gr.CheckboxGroup(choices=["Fast","HD"])
	return [output_file,ffmpeg]
	
app=gr.Interface(fn=convert,inputs=[gr.File(),gr.Radio(choices=["mp3","ogg","flac","wav"])],outputs=[gr.Audio(),"text"],flagging_dir="flagged")
app.launch(server_port=3000)
# cm=["ffmpeg","-i","/home/accel/Documents/Denouement.ogg","/home/accel/Documents/Denouement.mp3"]

# subprocess.run(cm,text=True)
# dm=gr.Blocks()
# with dm:
# 	gr.Markdown("Something")
# 	with gr.Tabs():
# 		with gr.TabItem("A tab"):
# 			text_input=gr.Textbox()
# 			text_output=gr.Textbox()
# 			text_button=gr.Button("Action")
# 		with gr.TabItem("Second tab"):
# 			with gr.Row():
# 				txt_input=gr.Textbox()
# 				txt_output=gr.Textbox()
# 				txt_button=gr.Button("Play")
# 	text_button.click(hello,inputs=text_input,outputs=text_output)
# dm.launch()

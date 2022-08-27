import json
from pprint import pprint
from tempfile import _TemporaryFileWrapper

import gradio as gr


def parse(param: json) -> dict:
    with open(param) as file:
        return json.load(file)


data = parse("./data.json")
codecs = parse("./codecs.json")

"""Video"""
containers=[j.get("name") for i in data["containers"] for j in data["containers"][i]]
video_containers = [i.get("name") for i in data["containers"]["video"]]
video_codecs = [i.get("name") for i in data["codecs"]["video"]]
video_aspect_ratio = [i.get("name") for i in data["aspects"]]
video_scaling = [i.get("name") for i in data["scalings"]]
""" Audio """
audio_containers = [i.get("name") for i in data["containers"]["audio"]]
audio_codecs = [i.get("name") for i in data["codecs"]["audio"]]
audio_channels = [i.get("name") for i in data["audioChannels"]]
audio_quality = [i.get("name") for i in data["audioQualities"]]
audio_sample_rates = [i.get("name") for i in data["sampleRates"]]

""" Video & Audio Filters """
# deband=[i.get("name") for i in data["deband"]]
# deflicker=[i.get("name") for i in data["deflicker"]]
# deshake=[i.get("name") for i in data["deshake"]]
# dejudder=[i.get("name") for i in data["dejudder"]]
# denoise=[i.get("name") for i in data["denoise"]]
# deinterlace=[i.get("name") for i in data["deinterlace"]]
filters = ["deband", "deflicker", "deshake",
           "dejudder", "denoise", "deinterlace"]
vf = [{vFilter: names} for vFilter in filters for names in [
    [i for i in data[vFilter]]]]

presets = [i.get("name") for i in data["presets"]]
profiles = [i.get("name") for i in data["profiles"]]
speeds = [i.get("name") for i in data["speeds"]]


outputMap = parse("./mappings.json")
"""Output Mappings of commands to value
   audioQuality -b:a 128k 
"""


class CommandBuilder():
    def __call__(self, *args, **kwds):
        return [i.value for i in self._component]

    def do(self, *inputs, **kwds):
        for comp in self._component:
            if comp.label is not None:
                self.startfunc(comp,"",comp.value)

    def __init__(self, *inputs: gr.Blocks) -> None:
        self.outputDict = {}
        self.formatOutputDict = {"vf": {}, "af": {}}
        # state=gr.Variable()
        # state2=gr.Variable()

        self._component: list[gr.components.Changeable] = []
        self.vf, self.af, self.extra = ([] for _ in range(3))
        self.commands = ""
        if inputs is None:
            return None
        for i in inputs:
            self._component += self._get_component_instance(i)
        for comp in self._component:
            state = gr.Variable()
            state2 = gr.Variable()
            if comp.label is not None:
                state.value = comp
                state2.value = comp.label
                comp.change(fn=self.changefunc, inputs=[
                            state, state2, comp], outputs=[])



    def update(self, Component: gr.components.IOComponent):
        for comp in self._component:
            comp.change(lambda: gr.update(
                value=self.commands), [], [Component])

    def _get_component_instance(self, inputs: gr.Blocks) -> "list[gr.components.Component]":
        return [gr.components.get_component_instance(i, render=True) for i in inputs.children if not hasattr(i, "children")]

    def setVideoFilters(self, options):
        value = self.outputDict.get(options, "-")
        filters = outputMap.get(options, None)
        arg = ""
        if options in ["deinterlace", "denoise"]:
            value = "_".join(value.lower().split())
            arg = filters.get(value, None)
            # self.vf.append(arg)
            self.formatOutputDict["vf"].update({options: arg})
            return True
        if options in ["deband", "deflicker", "deshake", "dejudder"]:
            arg = filters
            self.formatOutputDict["vf"].update({options: arg})
            return True

        return

    def setAudioFilters(self, options):
        value = self.outputDict.get(options, "-")
        if options in ["acontrast"]:
            value = int(value)/100
            arg = f"{options}={value}"

            self.formatOutputDict["af"].update({options: arg})
            return True
        return

    def setFormat(self, options):
        value = self.outputDict.get(options, "-")
        filters = outputMap.get(options, None)
        if options in ["video", "audio"]:
            value = "".join([i.get("value", "None") for i in data.get(
                "codecs").get(options) if i.get("name", None) == value])
            arg = f"{filters} {value}"
            self.formatOutputDict.update({options: arg})
            return True
        elif data.get(options) == None:
            arg = f"{filters} {value}"
            self.formatOutputDict.update({options: arg})
            return True
        elif options != "clip":
            value = "".join([i.get("value", "None") for i in data.get(
                options) if i.get("name", None) == value])
            arg = f"{filters} {value}"
            self.formatOutputDict.update({options: arg})

    def build(self):
        for i in self.outputDict:
            if self.setVideoFilters(i):
                continue
            elif self.setAudioFilters(i):
                continue
            else:
                self.setFormat(i)
        lst_extra, vf, af = ([] for _ in range(3))
        for val in self.formatOutputDict:
            if val == "vf":
                vf = self.formatOutputDict.get(val).values()
                vf = ",".join(list(vf))
            elif val == "af":
                af = self.formatOutputDict.get(val).values()
                af = ",".join(list(af))
            else:
                lst_extra.append(self.formatOutputDict.get(val))
        # print(lst_extra, "temp x")
        # if vf:self.vf=f"-vf '{vf}'"
        # if af:self.af=f"-af '{af}'"
        self.vf = f"-vf '{vf}'" if vf else ""
        self.af = f"-af '{af}'" if af else ""
        self.extra = " ".join(lst_extra)
        self.commands = f"{self.vf} {self.af} {self.extra}"

    def changefunc(self, input: gr.components.IOComponent, c_label="", newValue=""):
        label, *_ = input.label.strip(": ").lower().split(
        ) if type(input.label) != list else "".join(input.label).strip(": ").lower().split()
        label += "".join(_).title()
        if newValue not in [None, "Source", "Auto", "", "None",0]:
            self.outputDict.update({label: newValue})
        else:
            self.outputDict.pop(label, "No Key Exists")
            self.formatOutputDict["vf"].pop(label, "Key is None or similar")
            self.formatOutputDict["af"].pop(label, "Key is None or similar")
            self.formatOutputDict.pop(label, "Key is None or similar")
        self.build()
        print(self.commands,"   self.commands")
        print(self.vf, self.af, self.extra)
    def startfunc(self, input: gr.components.IOComponent, c_label="", newValue=""):
        label, *_ = input.label.strip(": ").lower().split(
        ) if type(input.label) != list else "".join(input.label).strip(": ").lower().split()
        label += "".join(_).title()
        if newValue not in [None, "Source", "Auto", "", "None",0]:
            self.outputDict.update({label: newValue})
        else:
            self.outputDict.pop(label, "No Key Exists")
            self.formatOutputDict["vf"].pop(label, "Key is None or similar")
            self.formatOutputDict["af"].pop(label, "Key is None or similar")
            self.formatOutputDict.pop(label, "Key is None or similar")
        self.build()




def somefunc(input: gr.components.IOComponent, c_label=""):
    label = ""
    output={}
    print(input, c_label)
    label, *_ = input.label.strip(": ").lower().split(
    ) if type(input.label) != list else "".join(input.label).strip(": ").lower().split()
    label += "".join(_).title()
    print(outputMap.get(label), label, c_label)
    if c_label not in [None, "Source", "Auto", ""]:
        print(input.value)
        output.update({label: c_label})
    else:
        output.pop(label, "No Key Exists")
    pprint(output)

# def mediaChange(option):
#     no_=gr.update(visible=False)
#     if option in video_containers:
#         output=gr.update(visible=True)
#         return [no_,output]
#     elif option in audio_containers:
#         output=gr.update(visible=True)
#         return [output,no_]
#     else:
#         output=gr.update(visible=False)
#         return [no_,no_]
def mediaChange(option):
    no_=gr.update(visible=False)
    output=gr.update(visible=True)
    ops={"Audio":gr.update(visible=True)}
    ops2={"Video":gr.update(visible=True)}
    ops3={"File":gr.update(visible=True,interactive=False)}
    # if option.lower()!="mp4" and option in video_containers:
    #     option="mp4"
    chosen=lambda x:x.get(option,gr.update(visible=False))
    print(chosen(ops2),ops2.get(option,no_))
    return [chosen(ops),chosen(ops2),chosen(ops3)]
def videoChange(value):
    print(value.name)

    # if option in video_containers:
    #     output=gr.update(visible=True)
    #     return [no_,output]
    # elif option in audio_containers:
    #     output=gr.update(visible=True)
    #     return [output,no_]
    # else:
    #     output=gr.update(visible=False)
    #     return [no_,no_]


def customBitrate(choice):
    if choice == "Custom":
        return gr.update(visible=True, value=None)
    else:
        return gr.update(visible=False, value=None)


def supported_codecs(format: str, a=data):
    # lst=[i for i in a["codecs"]["audio"]
    # if i.get("supported")==None or "ogg" in i["supported"]]
    if format:
        format = format.lower()
    video_lst = [val.get("name") for val in a["codecs"]["video"]
                 if val.get("supported") == None or format in val["supported"]]
    audio_lst = [val.get("name") for val in a["codecs"]["audio"]
                 if val.get("supported") == None or format in val["supported"]]
    return [gr.update(choices=video_lst), gr.update(choices=audio_lst)]


def supported_presets(format: str, a=data):
    if format:
        format = format.lower()
    video_lst = [val.get("name") for val in a["presets"]
                 if val.get("supported") == None or format in val["supported"]]
    print(format, video_lst)
    return gr.update(choices=video_lst)


"""Helper Functions for Processing """


def clear(*input):
    print(input, " clear_func")
    # for i in [inp for i in input for inp in i]:
    #     print(i, hasattr(i,"cleared_value"),type(i))
    # a=default_clear(input_components)
    def clear_func(x): return [component.cleared_value if hasattr(
        component, "cleared_value") else None for component in x]
    print(clear_func(input))
    return clear_func(input)


def change_clipbox(choice):
    print(gr.Dropdown().postprocess("clip test"))
    if choice == "Enabled":
        return [gr.update(visible=True, value="00:00"), gr.update(visible=True, value="00:10")]
    else:
        return [gr.update(visible=False, value=""), gr.update(visible=False, value="")]


def updateOutput(file: _TemporaryFileWrapper):
    if file:
        print(file.name)
        return gr.update(value=file.name)


def get_component_instance(inputs: gr.Blocks) -> list:
    return [gr.components.get_component_instance(i, render=True) for i in inputs.children]


class Clear(CommandBuilder):
    def __call__(self, *args, **kwds):
        return self._component

    def __str__(self):
        return f"{self._component} __clear__ class"

    def __repr__(self):
        return self._component

    def __init__(self, *input_component: gr.Blocks()) -> None:
        self._component = []
        if input_component is not None:
            for i in input_component:
                self._component += super()._get_component_instance(i)

    def __get_component_instance(self, inputs: gr.Blocks) -> list:
        # print(inputs, " class instance")
        # res=[]
        # for i in inputs.children:
        #     print(hasattr(i,"children"))
        #     if not (hasattr(i,"children")):
        #         res.append(gr.components.get_component_instance(i,render=True))
        #         print(i)
        #     elif hasattr(i,"children"):
        #         continue
        # return res
        return [gr.components.get_component_instance(i, render=True) for i in inputs.children if not hasattr(i, "children")]

    def add(self, *args):
        print(args, type(args))
        if args is not None:
            for i in args:
                self._component += self.__get_component_instance(i)
        return self._component

    def clear(self, *args):
        def clear_func(x): return [component.cleared_value if hasattr(
            component, "cleared_value") else component.value for component in x]
        return clear_func(self._component)

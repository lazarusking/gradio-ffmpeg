"""
util functions and classes
"""

import json
from tempfile import _TemporaryFileWrapper
from typing import List

import gradio as gr
from gradio.components import Component


def parse(param: json) -> dict:
    with open(param) as file:
        return json.load(file)


data = parse("./data.json")
codecs = parse("./codecs.json")

"""Video"""
containers = [j.get("name") for i in data["containers"] for j in data["containers"][i]]
video_containers = [i.get("name") for i in data["containers"]["video"]]
video_codecs = [i.get("value") for i in data["codecs"]["video"]]
video_aspect_ratio = [i.get("name") for i in data["aspects"]]
video_scaling = [i.get("name") for i in data["scalings"]]
""" Audio """
audio_containers = [i.get("name") for i in data["containers"]["audio"]]
audio_codecs = [i.get("value") for i in data["codecs"]["audio"]]
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
filters = ["deband", "deflicker", "deshake", "dejudder", "denoise", "deinterlace"]
vf = [{vFilter: names} for vFilter in filters for names in [[i for i in data[vFilter]]]]

presets = [i.get("name") for i in data["presets"]]
profiles = [i.get("name") for i in data["profiles"]]
speeds = [i.get("name") for i in data["speeds"]]


outputMap = parse("./mappings.json")
newoutputMap = parse("./new_mappings.json")
"""Output Mappings of commands to value
   audioQuality -b:a 128k
"""


class CommandBuilder:
    """Takes a collection of gradio layout elements and attaches
    a function to each component in the context
    to build an array of ffmpeg commands"""

    def __call__(self, *args, **kwds):
        return [i.value for i in self._component]

    def do(self, *inputs, **kwds):
        for comp in self._component:
            if comp.label is not None:
                self.changefunc(comp, "", comp.value)

    def reset(self):
        self.outputDict = {"vf": {}, "af": {}}
        self.commands = ""
        self.vf, self.af, self.extra = ([] for _ in range(3))

    def __init__(self, *inputs: gr.Blocks) -> None:
        """
        Parameters:
            *inputs: A tuple of layout blocks containing components(Textbox,Button...).
        """

        self.outputDict = {"vf": {}, "af": {}}
        self.formatOutputDict = {"vf": {}, "af": {}}
        # state=gr.Variable()
        # state2=gr.Variable()

        self._component: List[Component] = []
        self.vf, self.af, self.extra = ([] for _ in range(3))
        self.commands = ""
        if inputs is None:
            return None
        for i in inputs:
            self._component += self._get_component_instance(i)
        for comp in self._component:
            state = gr.State()
            state2 = gr.State()
            if comp.label is not None:
                state.value = comp
                state2.value = comp.label
                comp.change(
                    fn=self.changefunc, inputs=[state, state2, comp], outputs=[]
                )

    def changefunc(self, input: gr.components.Component, c_label="", newValue=""):
        label, *_ = (
            input.label.strip(": \n").lower().split()
            if not isinstance(input.label, list)
            else "".join(input.label).strip(": ").lower().split()
        )
        label += "".join(_).title()
        key = newoutputMap.get(label)
        lst_extra, vf, af = ([] for _ in range(3))
        if newValue not in [None, "Source", "Auto", "", "None", "none", 0]:
            self.setVf(label, newValue)
            self.setAf(label, newValue)
            self.setF(label, newValue)
            for val in self.outputDict:
                if val == "vf":
                    vf = self.outputDict.get(val).values()
                    vf = ",".join(list(vf))
                elif val == "af":
                    af = self.outputDict.get(val).values()
                    af = ",".join(list(af))
                    pass
                else:
                    lst_extra.extend([val, self.outputDict.get(val)])

        else:
            self.outputDict.pop(key, "No Key Exists")
            self.outputDict["vf"].pop(label, "No Key Exists")
            self.outputDict["af"].pop(label, "No Key Exists")
        self.vf = f"-vf '{vf}'" if vf else ""
        self.af = f"-af '{af}'" if af else ""
        self.extra = " ".join(lst_extra)
        self.commands = f"{self.vf} {self.af} {self.extra}"

        print(self.vf, self.af, self.extra)

    def setVf(self, label: str, newValue: "str| int"):
        """Sets Video filters

        Args:
            label : label of components
            newValue : value of component
        """
        if newoutputMap["vf"].get(label):
            key = newoutputMap["vf"].get(label)
            if label in ["deinterlace", "denoise"]:
                value = "_".join(newValue.lower().split())
                arg = key.get(value, None)
                self.outputDict["vf"].update({label: arg})
            else:
                self.outputDict["vf"].update({key: key})

    def setF(self, label, newValue):
        """Sets Extra filters
        Args:
            label : label of components
            newValue : value of component
        """
        if newoutputMap.get(label):
            key = newoutputMap.get(label)
            if label in ["video", "audio"]:
                value = codecs.get(label).get(newValue, newValue)
                print(value)
                self.outputDict.update({key: value})
            elif label in ["startTime", "stopTime"]:
                self.outputDict.update({key: newValue})
            else:
                value = "".join(
                    [
                        i.get("value", "None")
                        for i in data.get(label)
                        if i.get("name", None) == newValue
                    ]
                )
                self.outputDict.update({key: value})

    def setAf(self, label: str, newValue: "str|int"):
        """Sets Extra filters
        Args:
            label : label of components
            newValue : value of component
        """
        if newoutputMap["af"].get(label):
            value = int(newValue) / 100
            arg = f"{label}={value}"
            self.outputDict["af"].update({label: arg})

    def update(self, Component: Component):
        for comp in self._component:
            print(comp, "comp")
            comp.change(lambda: gr.update(value=self.outputDict), [], [Component])

    def _get_component_instance(self, inputs: gr.Blocks) -> List[Component]:
        """
        returns components present in a layout block
        Parameters:
            inputs: layout block
        """
        res = []
        for i in inputs.children:
            # print(i,hasattr(i,"children"))
            if not (hasattr(i, "children")):
                # res.append(gr.components.get_component_instance(i,render=True))
                res += [gr.components.get_component_instance(i, render=True)]
                # print(res)
            elif hasattr(i, "children"):
                res += self._get_component_instance(i)
        # print(res)
        return res
        # return [gr.components.get_component_instance(i, render=True) for i in inputs.children if not hasattr(i, "children")]

    def setVideoFilters(self, options):
        value = self.outputDict.get(options, "-")
        filters = newoutputMap.get(options, None)
        arg = ""
        if options in ["deinterlace", "denoise"]:
            value = "_".join(value.lower().split())
            arg = filters.get(value, None)
            # self.vf.append(arg)
            self.outputDict["vf"].update({options: arg})
            return True
        if options in ["deband", "deflicker", "deshake", "dejudder"]:
            arg = filters
            self.outputDict["vf"].update({options: arg})
            return True

        return

    def setAudioFilters(self, options):
        value = self.outputDict.get(options, "-")
        if options in ["acontrast"]:
            value = int(value) / 100
            arg = f"{options}={value}"

            self.outputDict["af"].update({options: arg})
            return True
        return

    def setFormat(self, options):
        value = self.outputDict.get(options, "-")
        filters = newoutputMap.get(options, None)
        if options in ["video", "audio"]:
            value = "".join(
                [
                    i.get("value", "None")
                    for i in data.get("codecs").get(options)
                    if i.get("name", None) == value
                ]
            )
            arg = f"{filters} {value}"
            self.outputDict.update({options: arg})
            return True
        elif data.get(options) is None:
            arg = f"{filters} {value}"
            self.outputDict.update({options: arg})
            return True
        elif options != "clip":
            value = "".join(
                [
                    i.get("value", "None")
                    for i in data.get(options)
                    if i.get("name", None) == value
                ]
            )
            arg = f"{filters} {value}"
            self.outputDict.update({options: arg})

    def build(self):
        for i in self.outputDict:
            if self.setVideoFilters(i):
                continue
            elif self.setAudioFilters(i):
                continue
            else:
                self.setFormat(i)
        lst_extra, vf, af = ([] for _ in range(3))
        for val in self.outputDict:
            if val == "vf":
                vf = self.outputDict.get(val).values()
                vf = ",".join(list(vf))
            elif val == "af":
                af = self.outputDict.get(val).values()
                af = ",".join(list(af))
            else:
                lst_extra.append(self.outputDict.get(val))
        # print(lst_extra, "temp x")
        # if vf:self.vf=f"-vf '{vf}'"
        # if af:self.af=f"-af '{af}'"
        self.vf = f"-vf '{vf}'" if vf else ""
        self.af = f"-af '{af}'" if af else ""
        self.extra = " ".join(lst_extra)
        self.commands = f"{self.vf} {self.af} {self.extra}"

    def startfunc(self, input: gr.components.Component, c_label="", newValue=""):
        label, *_ = (
            input.label.strip(": ").lower().split()
            if not isinstance(input.label, list)
            else "".join(input.label).strip(": ").lower().split()
        )
        label += "".join(_).title()
        if newValue not in [None, "Source", "Auto", "", "None", 0]:
            self.outputDict["vf"].update({label: newValue})
            self.outputDict["af"].update({label: newValue})
            self.outputDict.update({label: newValue})
        else:
            self.outputDict.pop(label, "No Key Exists")
            self.outputDict["vf"].pop(label, "No Key Exists")
            self.outputDict["af"].pop(label, "No Key Exists")
            # self.formatOutputDict["vf"].pop(label, "Key is None or similar")
            # self.formatOutputDict["af"].pop(label, "Key is None or similar")
            # self.formatOutputDict.pop(label, "Key is None or similar")
        print(self.outputDict)
        self.build()


# def somefunc(input: gr.components.IOComponent, c_label=""):
#     label = ""
#     output = {}
#     print(input, c_label)
#     label, *_ = input.label.strip(": ").lower().split(
#     ) if type(input.label) != list else "".join(input.label).strip(": ").lower().split()
#     label += "".join(_).title()
#     print(newoutputMap.get(label), label, c_label)
#     if c_label not in [None, "Source", "Auto", ""]:
#         print(input.value)
#         output.update({label: c_label})
#     else:
#         output.pop(label, "No Key Exists")
#     pprint(output)

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


def mediaChange(option: str, state) -> List[Component]:
    """
        Allows playing the media in various options,
        Video, Audio or File

    Args:
        option : Clicked buttons value

    Returns:
        List[Component]: list of toggled output components to display
    """
    print(state, "state")
    ops = {"Audio": gr.update(visible=True, value=state)}
    ops2 = {"Video": gr.update(visible=True, value=state)}
    ops3 = {"File": gr.update(visible=True, value=state, interactive=False)}

    def chosen(x):
        return x.get(option, gr.update(visible=False))

    return [chosen(ops), chosen(ops2), chosen(ops3)]


# def videoChange(value):
#     print(value.name)

# if option in video_containers:
#     output=gr.update(visible=True)
#     return [no_,output]
# elif option in audio_containers:
#     output=gr.update(visible=True)
#     return [output,no_]
# else:
#     output=gr.update(visible=False)
#     return [no_,no_]


"""Helper Functions for Processing """


# def clear(*input):
#     print(input, " clear_func")
#     # for i in [inp for i in input for inp in i]:
#     #     print(i, hasattr(i,"cleared_value"),type(i))
#     # a=default_clear(input_components)
#     def clear_func(x): return [component.cleared_value if hasattr(
#         component, "cleared_value") else None for component in x]
#     print(clear_func(input))
#     return clear_func(input)


def customBitrate(choice: int) -> Component:
    """
        Toggle a component for custom Audio Quality
        visible/none
    Args:
        choice : Custom audio quality

    Returns:
        Component: component toggle state
    """
    if choice == "Custom":
        return gr.update(visible=True)
    else:
        return gr.update(visible=False, value=0)


def supported_codecs(format: str) -> List[Component]:
    """
        Changes video and audio components with appropriate
        options according to passed format

    Args:
        format: passed media codec (x264,x265)

    Returns:
        List[Component]: list of components with updated choices
    """
    if format:
        format = format.lower()
    video_lst = [
        val.get("value")
        for val in data["codecs"]["video"]
        if val.get("supported") is None or format in val["supported"]
    ]
    audio_lst = [
        val.get("value")
        for val in data["codecs"]["audio"]
        if val.get("supported") is None or format in val["supported"]
    ]
    return [gr.Dropdown(choices=video_lst), gr.Dropdown(choices=audio_lst)]


def supported_presets(format: str) -> Component:
    """
        Changes presets component with appropriate
        options according to passed format
    Args:
        format: passed media codec (x264,x265)

    Returns:
        Component: component with updated choice list (video codecs)
    """
    if format:
        format = format.lower()
    print(format, "preset")
    video_lst = [
        val.get("name")
        for val in data["presets"]
        if val.get("supported") is None or format in val["supported"]
    ]
    return gr.Dropdown(choices=video_lst)


def change_clipbox(choice: str) -> List[Component]:
    """
    Toggles the clipping Textbox

    Args:
        choice: Enabled/None

    Returns:
        List[Component]: list of components with visible state of the clip components
    """
    print(choice, " now choice")
    if choice == "Enabled":
        return [
            # gr.update(visible=True, value="00:00"),
            # gr.update(visible=True, value="00:10"),
            gr.Textbox(
                label="Start Time:", placeholder="00:00", visible=True, value="00:00"
            ),
            gr.Textbox(
                label="Stop Time:", placeholder="00:00", visible=True, value="00:10"
            ),
        ]
    else:
        return [
            gr.Textbox(visible=False, value=""),
            gr.Textbox(visible=False, value=""),
        ]


def updateOutput(file: _TemporaryFileWrapper) -> Component:
    if file:
        print(file.name)
        return gr.update(value=file.name)


def get_component_instance(inputs: gr.Blocks) -> List[Component]:
    """returns only components

    Args:
        inputs: layout elements

    Returns:
        List[Component]: components
    """
    return [
        gr.components.get_component_instance(i, render=True) for i in inputs.children
    ]


class Clear(CommandBuilder):
    """Class for clearing components in layouts"""

    def __call__(self, *args, **kwds):
        return self._component

    def __str__(self):
        return f"{self._component} __clear__ class"

    def __repr__(self):
        return self._component

    def __init__(self, *input_component: gr.Blocks) -> None:
        """
        Parameters:
            *input_component: A tuple of layout blocks containing components
        """
        self._component = []
        if input_component is not None:
            for i in input_component:
                # self._component += super()._get_component_instance(i)
                self._component += self.__get_component_instance(i)

    def __get_component_instance(self, inputs: gr.Blocks) -> list:
        # print(inputs, " class instance")
        res = []
        # print(*inputs.children)
        for i in inputs.children:
            # print(i,hasattr(i,"children"))
            if not (hasattr(i, "children")):
                # res.append(gr.components.get_component_instance(i,render=True))
                res += [gr.components.get_component_instance(i, render=True)]
                # print(i)
            elif hasattr(i, "children"):
                # print(*i.children)
                res += self.__get_component_instance(i)
                # res=[gr.components.get_component_instance(i, render=True) for i in inputs.children if not hasattr(i, "children")]
                # print(res,"__ result")
        # print(res)
        return res
        # return [gr.components.get_component_instance(i, render=True) for i in inputs.children if not hasattr(i, "children")]

    def add(self, *args):
        print(args, type(args))
        if args is not None:
            for i in args:
                self._component += self.__get_component_instance(i)
        return self._component

    def clear(self, *args):
        """
        Function to clear components from a Block in the class instance
        """

        def clear_func(x):
            return [
                (
                    component.cleared_value
                    if hasattr(component, "cleared_value")
                    else component.value
                )
                for component in x
            ]

        return clear_func(self._component)

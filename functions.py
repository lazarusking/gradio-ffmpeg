"""
util functions and classes
"""

import json
from tempfile import _TemporaryFileWrapper
from typing import List

import gradio as gr
from gradio.components import Component


def parse(param: str) -> dict:
    with open(param, encoding="utf-8") as file:
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
video_filters = ["deband", "deflicker", "deshake", "dejudder", "denoise", "deinterlace"]
VF = [{vFilter: names} for vFilter in video_filters for names in [list(data[vFilter])]]

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

    def __init__(self, *inputs: gr.Row | gr.Column) -> None:
        """
        Parameters:
            *inputs: A tuple of layout blocks containing components(Textbox,Button...).
        """

        self.output_dict = {"vf": {}, "af": {}}
        self.formatoutputdict = {"vf": {}, "af": {}}

        self._component: List[Component] = []
        self.vf, self.af, self.extra = ([] for _ in range(3))
        self.commands = ""
        if inputs is None:
            return None
        for i in inputs:
            self._component += self._get_component_instance(i)
        # for comp in self._component:
        #     state = gr.State()
        #     if comp.label is not None:
        #         state.value = comp.label
        #         comp.change(fn=self.changefunc, inputs=[state, comp], outputs=[])
        # self.changefunc(state.value, comp.value)
        # comp.change(fn=self.changefunc, inputs=[state, comp], outputs=[])

    def __call__(self, *args, **kwds):
        return [i.value for i in self._component]

    def setup_listener(self, *inputs, **kwds):
        """
        Sets up listeners for component updates in the current instance.

        """
        for comp in self._component:
            if comp.label is not None:
                # self.changefunc(comp, comp.value)
                # print(
                #     comp.label,
                #     comp,
                # )
                state = gr.State(value=comp.label)
                comp.change(fn=self.changefunc, inputs=[state, comp], outputs=[])

    def reset(self):
        self.output_dict = {"vf": {}, "af": {}}
        self.commands = ""
        self.vf, self.af, self.extra = ([] for _ in range(3))

    def changefunc(self, component_label: str | None, new_value=""):
        label, *_ = (
            component_label.strip(": \n").lower().split()
            if component_label
            else ""
            if not isinstance(component_label, list)
            else "".join(component_label).strip(": ").lower().split()
        )
        label += "".join(_).title()
        key = newoutputMap.get(label, "")
        lst_extra, vf, af = ([] for _ in range(3))
        if new_value not in [None, "Source", "Auto", "", "None", "none", 0]:
            self.set_vf(label, new_value)
            self.set_af(label, new_value)
            self.set_f(label, new_value)
            for val in self.output_dict:
                if val == "vf":
                    vf = self.output_dict.get(val, {}).values()
                    vf = ",".join(list(vf))
                elif val == "af":
                    af = self.output_dict.get(val, {}).values()
                    af = ",".join(list(af))
                else:
                    lst_extra.extend([val, self.output_dict.get(val)])

        else:
            self.output_dict.pop(key, "No Key Exists")
            self.output_dict["vf"].pop(label, "No Key Exists")
            self.output_dict["af"].pop(label, "No Key Exists")
        self.vf = f"-vf '{vf}'" if vf else ""
        self.af = f"-af '{af}'" if af else ""
        self.extra = " ".join(lst_extra)
        self.commands = " ".join(f"{self.vf} {self.af} {self.extra}".strip().split())
        # self.commands = " ".join(filter(None, [self.vf, self.af, self.extra]))

        print(self.vf, self.af, self.extra)

    def set_vf(self, label: str, new_value: "str| int"):
        """Sets Video filters

        Args:
            label : label of components
            newValue : value of component
        """
        if newoutputMap["vf"].get(label):
            key = newoutputMap["vf"].get(label)
            if label in ["deinterlace", "denoise"]:
                value = "_".join(str(new_value).lower().split())
                arg = key.get(value, None)
                self.output_dict["vf"].update({label: arg})
            else:
                self.output_dict["vf"].update({key: key})

    def set_f(self, label: str, new_value: "str| int"):
        """Sets Extra filters
        Args:
            label : label of components
            newValue : value of component
        """
        if newoutputMap.get(label):
            key = newoutputMap.get(label, "")
            if label in ["video", "audio"]:
                codec_label = codecs.get(label)
                value = (
                    codec_label.get(new_value, new_value) if codec_label else new_value
                )
                print(value)
                self.output_dict.update({key: value})
            elif label in ["startTime", "stopTime"]:
                self.output_dict.update({key: new_value})
            else:
                value = "".join(
                    [
                        i.get("value", "None")
                        for i in data.get(label, [])
                        if i.get("name", None) == new_value
                    ]
                )
                self.output_dict.update({key: value})

    def set_af(self, label: str, new_value: "str|int"):
        """Sets Audio filters
        Args:
            label : label of components
            newValue : value of component
        """
        if newoutputMap["af"].get(label):
            value = int(new_value) / 100
            arg = f"{label}={value}"
            self.output_dict["af"].update({label: arg})

    def update(self, component: Component):
        for comp in self._component:
            # print(comp, "comp")
            comp.change(
                lambda: gr.update(value=f"$ {self.commands}"),
                [],
                [component],
            )

    def _get_component_instance(self, inputs: gr.Row | gr.Column) -> List[Component]:
        """
        returns components present in a layout block
        Parameters:
            inputs: layout block
        """
        res = []
        for i in inputs.children:
            # print(i,hasattr(i,"children"))
            # print(
            #     type(i),
            #     "type",
            #     # isinstance(i, gr.components.Component),
            #     # isinstance(i, gr.Blocks),
            #     hasattr(i, "children"),
            # )
            if not hasattr(i, "children"):
                # res.append(gr.components.get_component_instance(i,render=True))
                # if isinstance(i, gr.components.Component):
                res += [gr.components.get_component_instance(i)]
            else:
                res += self._get_component_instance(i)
        # print(res)
        return res

    def set_video_filters(self, options):
        value = self.output_dict.get(options, "-")
        filters = newoutputMap.get(options, None)
        arg = ""
        if options in ["deinterlace", "denoise"]:
            value = "_".join(value.lower().split())
            arg = filters.get(value, None)
            # self.vf.append(arg)
            self.output_dict["vf"].update({options: arg})
            return True
        if options in ["deband", "deflicker", "deshake", "dejudder"]:
            arg = filters
            self.output_dict["vf"].update({options: arg})
            return True

        return False

    def set_audio_filters(self, options):
        value = self.output_dict.get(options, "-")
        if options in ["acontrast"]:
            value = int(value) / 100
            arg = f"{options}={value}"

            self.output_dict["af"].update({options: arg})
            return True
        return

    def set_format(self, options):
        value = self.output_dict.get(options, "-")
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
            self.output_dict.update({options: arg})
            return True
        elif data.get(options) is None:
            arg = f"{filters} {value}"
            self.output_dict.update({options: arg})
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
            self.output_dict.update({options: arg})

    def build(self):
        for i in self.output_dict:
            if self.set_video_filters(i):
                continue
            elif self.set_audio_filters(i):
                continue
            else:
                self.set_format(i)
        lst_extra, vf, af = ([] for _ in range(3))
        for val in self.output_dict:
            if val == "vf":
                vf = self.output_dict.get(val).values()
                vf = ",".join(list(vf))
            elif val == "af":
                af = self.output_dict.get(val).values()
                af = ",".join(list(af))
            else:
                lst_extra.append(self.output_dict.get(val))
        # print(lst_extra, "temp x")
        # if vf:self.vf=f"-vf '{vf}'"
        # if af:self.af=f"-af '{af}'"
        self.vf = f"-vf '{vf}'" if vf else ""
        self.af = f"-af '{af}'" if af else ""
        self.extra = " ".join(lst_extra)
        self.commands = f"{self.vf} {self.af} {self.extra}"

    def startfunc(self, component: gr.components.Component, new_value=""):
        label, *_ = (
            component.label.strip(": ").lower().split()
            if not isinstance(component.label, list)
            else "".join(component.label).strip(": ").lower().split()
        )
        label += "".join(_).title()
        if new_value not in [None, "Source", "Auto", "", "None", 0]:
            self.output_dict["vf"].update({label: new_value})
            self.output_dict["af"].update({label: new_value})
            self.output_dict.update({label: new_value})
        else:
            self.output_dict.pop(label, "No Key Exists")
            self.output_dict["vf"].pop(label, "No Key Exists")
            self.output_dict["af"].pop(label, "No Key Exists")
            # self.formatOutputDict["vf"].pop(label, "Key is None or similar")
            # self.formatOutputDict["af"].pop(label, "Key is None or similar")
            # self.formatOutputDict.pop(label, "Key is None or similar")
        print(self.output_dict)
        self.build()


def media_change(option: str, state) -> List[Component]:
    """
        Allows playing the media in various options,
        Video, Audio or File

    Args:
        option : Clicked buttons value

    Returns:
        List[Component]: list of toggled output components to display
    """
    print(state, "state")
    ops = {"Audio": gr.Audio(visible=True, value=state)}
    ops2 = {"Video": gr.Video(visible=True, value=state)}
    ops3 = {"File": gr.File(visible=True, value=state, interactive=False)}

    def chosen(x: dict) -> Component:
        return x.get(option, gr.update(visible=False))

    return [chosen(ops), chosen(ops2), chosen(ops3)]


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


def set_custom_bitrate(choice: int) -> Component:
    """
        Toggle a component for custom Audio Quality
        visible/none
    Args:
        choice : Custom audio quality

    Returns:
        Component: component toggle state
    """
    if choice == "Custom":
        return gr.Number(visible=True)
    return gr.Number(visible=False, value=0)


def supported_codecs(codec: str) -> List[Component]:
    """
        Changes video and audio components with appropriate
        options according to passed format

    Args:
        format: passed media codec (x264,x265)

    Returns:
        List[Component]: list of components with updated choices
    """
    if codec:
        codec = codec.lower()
    video_lst = [
        val.get("value")
        for val in data["codecs"]["video"]
        if val.get("supported") is None or codec in val["supported"]
    ]
    audio_lst = [
        val.get("value")
        for val in data["codecs"]["audio"]
        if val.get("supported") is None or codec in val["supported"]
    ]
    return [gr.Dropdown(choices=video_lst), gr.Dropdown(choices=audio_lst)]


def supported_presets(preset: str) -> Component:
    """
        Changes presets component with appropriate
        options according to passed format
    Args:
        format: passed media codec (slow,fast,ultrafast)

    Returns:
        Component: component with updated choice list (video codecs)
    """
    if preset:
        preset = preset.lower()
    print(preset, "preset")
    video_lst = [
        val.get("name")
        for val in data["presets"]
        if val.get("supported") is None or preset in val["supported"]
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


# def updateOutput(file: _TemporaryFileWrapper) -> Component:
#     if file:
#         print(file.name)
#         return gr.update(value=file.name)


class Clear(CommandBuilder):
    """Class for clearing components in layouts"""

    def __init__(self, *input_component: gr.Row | gr.Column) -> None:
        """
        Parameters:
            *input_component: A tuple of layout blocks containing components
        """
        super().__init__(*input_component)
        self._component = []
        if input_component is not None:
            for i in input_component:
                # self._component += super()._get_component_instance(i)
                self._component += self.__get_component_instance(i)

    def __call__(self, *args, **kwds):
        return self._component

    def __str__(self):
        return f"{self._component} __clear__ class"

    def __get_component_instance(self, inputs: gr.Row | gr.Column) -> list:
        res = []
        for i in inputs.children:
            # print(i,hasattr(i,"children"))
            if not hasattr(i, "children"):
                # res.append(gr.components.get_component_instance(i,render=True))
                res += [gr.components.get_component_instance(i)]
                # print(i)
            else:
                res += self.__get_component_instance(i)
                # res=[gr.components.get_component_instance(i, render=True) for i in inputs.children if not hasattr(i, "children")]
        # print(res)
        return res

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

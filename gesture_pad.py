from tkinter.filedialog import *
from tkinter import messagebox
from backend.gesture_pad_be import Backend
from utils.config_helper import read_config


class GesturePad:

    def __init__(self, width=600, height=400):
        c, _ = read_config()
        backend = Backend(mediapipe_dir=c["mediapipe_dir"],
                          audio_path="tmp/integration_audio.wav",
                          video_path="tmp/integration_video.mp4",
                          mp_video_path="tmp/integration_video_mp.mp4",
                          gestures_dir="tmp/integration_frames",
                          gesture_prefix="image",
                          debug=False)
        self.__backend = backend

        self.__root = Tk()
        self.__file = None
        # default window width and height
        self.__thisTextArea = Text(self.__root)
        self.__thisScrollBar = Scrollbar(self.__thisTextArea)
        self.__thisMenuBar = Menu(self.__root)
        self.__thisFileMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__thisEditMenu = Menu(self.__thisMenuBar, tearoff=0)
        self.__recording = False
        self.__audio = None
        self.__video = None
        try:
            self.__root.wm_iconbitmap("Notepad.ico")
        except:
            pass

        self.__thisWidth = width
        self.__thisHeight = height
        self.__root.title("Untitled - GesturePad")

        # Center the window
        screenWidth = self.__root.winfo_screenwidth()
        screenHeight = self.__root.winfo_screenheight()

        # For left-alling
        left = (screenWidth / 2) - (self.__thisWidth / 2)

        # For right-allign
        top = (screenHeight / 2) - (self.__thisHeight / 2)

        # For top and bottom
        self.__root.geometry('%dx%d+%d+%d' % (self.__thisWidth, self.__thisHeight, left, top))

        self.__root.grid_rowconfigure(0, weight=1)
        self.__root.grid_columnconfigure(0, weight=1)

        self.__thisTextArea.grid(sticky=N + E + S + W)

        self.__thisFileMenu.add_command(label="New",
                                        command=self.__newFile)

        self.__thisFileMenu.add_command(label="Open",
                                        command=self.__openFile)

        self.__thisFileMenu.add_command(label="Save",
                                        command=self.__saveFile)

        self.__thisFileMenu.add_separator()
        self.__thisFileMenu.add_command(label="Exit",
                                        command=self.__quitApplication)

        self.__thisMenuBar.add_cascade(label="File",
                                       menu=self.__thisFileMenu)

        self.__thisEditMenu.add_command(label="Cut",
                                        command=self.__cut)

        self.__thisEditMenu.add_command(label="Copy",
                                        command=self.__copy)

        self.__thisEditMenu.add_command(label="Paste",
                                        command=self.__paste)

        self.__thisMenuBar.add_cascade(label="Edit",
                                       menu=self.__thisEditMenu)

        self.__thisMenuBar.add_command(label="Rec",
                                       command=self.__rec)

        self.__root.config(menu=self.__thisMenuBar)

        self.__thisScrollBar.pack(side=RIGHT, fill=Y)

        # Scrollbar will adjust automatically according to the content
        self.__thisScrollBar.config(command=self.__thisTextArea.yview)
        self.__thisTextArea.config(yscrollcommand=self.__thisScrollBar.set)

    def __quitApplication(self):
        self.__root.destroy()

    def __openFile(self):
        self.__file = askopenfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Text Documents",
                                                                                                 "*.txt")])

        if self.__file == "":
            self.__file = None
        else:
            self.__root.title(os.path.basename(self.__file) + " - Notepad")
            self.__thisTextArea.delete(1.0, END)
            file = open(self.__file, "r")
            self.__thisTextArea.insert(1.0, file.read())
            file.close()

    def __newFile(self):
        self.__root.title("Untitled - Notepad")
        self.__file = None
        self.__thisTextArea.delete(1.0, END)

    def __saveFile(self):
        if self.__file is None:
            self.__file = asksaveasfilename(initialfile='Untitled.html',
                                            defaultextension=".html",
                                            filetypes=[("All Files", "*.*"),
                                                       ("Text Documents", "*.txt")])
            if self.__file == "":
                self.__file = None
            else:

                # Try to save the file
                file = open(self.__file, "w")
                file.write(self.__thisTextArea.get(1.0, END))
                file.close()

                # Change the window title
                self.__root.title(os.path.basename(self.__file) + " - Notepad")


        else:
            file = open(self.__file, "w")
            file.write(self.__thisTextArea.get(1.0, END))
            file.close()

    def __cut(self):
        self.__thisTextArea.event_generate("<<Cut>>")

    def __copy(self):
        self.__thisTextArea.event_generate("<<Copy>>")

    def __paste(self):
        self.__thisTextArea.event_generate("<<Paste>>")

    def __rec(self):
        """
        Starts the audio/video processing of the user input.
        """

        if self.__recording is False:
            self.__video, self.__audio = self.__backend.start_recording()
            self.__recording = True
            self.__thisMenuBar.entryconfigure(3, label="Stop")
        else:
            try:
                v, a = self.__backend.stop_recording(self.__video, self.__audio)
                frames, timings = self.__backend.preprocess_video(v)
                words_op = self.__backend.send_audio(audio_input=a)
                g_list = self.__backend.process_video(frame_paths=frames, gesture_timings=timings)
                w_list = self.__backend.process_audio_response(operation=words_op)
                fused = self.__backend.fuse(gestures=g_list, words=w_list)
                formatted = self.__backend.apply_format(multimodal_stream=fused)
                print(formatted)
                self.__thisTextArea.insert(CURRENT, formatted)
            except Exception as e:
                messagebox.showerror(title="Error", message="Error during audio/video processing")
            self.__recording = False
            self.__thisMenuBar.entryconfigure(3, label="Rec")

    def run(self):
        # Run main application
        self.__root.mainloop()


# Run main application
if __name__ == "__main__":
    gesturepad = GesturePad()
    gesturepad.run()

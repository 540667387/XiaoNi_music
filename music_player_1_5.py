"""
@author: xuji0003
@file: music_player_1_5.py
@Description: 新增qq，网易云音乐，加了去重排序算法
@time: 2021/6/17
"""

"""
pyinstaller -F -i  static/qiaoba.ico music_player_1_5.py --noconsole --hidden-import=addons.migu  --hidden-import=addons.netease --hidden-import=addons.qq
"""

import os
import threading
import time
import tkinter.messagebox
from tkinter import *
from ttkthemes import *
import tkinter.ttk as ttk
from main_songs import *
from mutagen.mp3 import MP3
import pygame
from PIL import Image
from PIL import ImageTk
import random
from utils import get_list_index, parseLrc, getPageIndexs
from subprocess import call

import inspect
import ctypes
from interval import Interval


class MusicPlayer:
    global str_obj_dict
    str_obj_dict = {}
    global pageBtns
    pageBtns = []
    global thread_list
    thread_list = []
    global song_file_path
    song_file_path = ""
    global lrc_file_path
    lrc_file_path = ""
    global current_time
    current_time = 0
    global lrc_thread_list
    lrc_thread_list = []
    global history_dict
    history_dict = {}
    global history_index
    history_index = -1
    global page_count
    page_count = 20

    def selectfile(self):
        v.set(1)
        keywords = entry.get()
        init(keywords, pageNo=v.get())
        songs_list = getSongList()
        totalCount = len(songs_list)
        str_obj_dict.clear()
        for pageBtn in pageBtns:
            pageBtn.destroy()
        pageBtns.clear()
        for num in range(1, int(int(totalCount) / page_count) + 1):
            radionBtn = tkinter.Radiobutton(leftframe, text=num, variable=v, value=num, indicatoron=False,
                                            command=fc.click_paging)
            radionBtn.pack(side=LEFT)
            pageBtns.append(radionBtn)

        playlistbox.delete(0, END)
        for song in songs_list:
            str_obj_dict[str(song)] = song
        for i in getPageIndexs(v.get(), page_count):
            if len(str_obj_dict.keys()) > i:
                playlistbox.insert(END, list(str_obj_dict.keys())[i])

    def click_paging(self):
        playlistbox.delete(0, END)
        for i in getPageIndexs(v.get(), page_count):
            if len(str_obj_dict.keys()) > i:
                playlistbox.insert(END, list(str_obj_dict.keys())[i])

    def play_music(self):
        global paused, currentsong, song_file_path, lrc_file_path, history_dict, history_index
        if playlistbox.get(ACTIVE) == currentsong:
            if paused:
                currentsong = playlistbox.get(ACTIVE)
                pygame.mixer.music.pause()
                statusbar['text'] = "暂停播放"
                paused = FALSE
                playBtn.configure(image=playPhoto)
            else:
                pygame.mixer.music.unpause()
                statusbar['text'] = "正在播放" + ' - ' + os.path.basename(song_file_path)
                paused = TRUE
                playBtn.configure(image=pausePhoto)

        else:
            try:
                paused = FALSE
                self.stop_music()
                # time.sleep(1)
                currentsong = playlistbox.get(ACTIVE)
                history_index += 1
                history_dict[history_index] = currentsong
                self.downloadAndPlay()
            except Exception as e:
                print(str(e))
                if str(e) == 'mpg123_seek: Invalid RVA mode. (code 12)':
                    tkinter.messagebox.showerror('播放错误', '当前歌曲的格式错误,请播放其他歌曲！！!')
                else:
                    tkinter.messagebox.showerror('播放错误', '播放列表里没有歌曲，请查询！！！')

    def play_mode(self):
        try:
            global currentsong, song_file_path, lrc_file_path, history_index, history_dict
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == NEXT:
                        play_list = list(playlistbox.get(0, playlistbox.size() - 1))
                        # order
                        if musicMode == 0:
                            index = get_list_index(play_list, currentsong, -1)
                            pre_play_list = play_list[0:index + 1]
                            beh_play_list = play_list[index + 1:]
                            beh_play_list.extend(pre_play_list)
                            play_list = beh_play_list
                            currentsong = play_list[0]
                        # single
                        elif musicMode == 1:
                            currentsong = currentsong
                        # random
                        elif musicMode == 2:
                            currentsong = random.choice(play_list)
                        # print("Play:", currentsong)
                        history_index += 1
                        history_dict[history_index] = currentsong
                        self.downloadAndPlay()
                        progress_bar_scale.set(0)
                    elif event.type == STOP:
                        continue
        except Exception as e:
            print(str(e))
            if str(e) == 'mpg123_seek: Invalid RVA mode. (code 12)':
                tkinter.messagebox.showerror('播放错误', '当前歌曲的格式错误,请播放其他歌曲！！!')
            else:
                tkinter.messagebox.showerror('播放错误', '请联系jiawei.Xu！！！')

    def downloadAndPlay(self):
        global song_file_path, lrc_file_path, currentsong, paused
        playBtn.configure(image=pausePhoto)
        paused = TRUE
        songs_path_list, lyrics_path_list, cover_path_list = download([str_obj_dict[currentsong]])
        song_file_path = songs_path_list[0]
        if song_file_path.split('.')[-1] == 'm4a':
            outfile_name = song_file_path.split('.')[0:-1][0] + ".mp3"
            ffmpeg_command = '{} -y "{}" -i "{}" -codec:a libmp3lame -qscale:a 1'.format(os.path.join(os.path.dirname(sys.executable),"static","ffmpeg"),outfile_name,
                                                                                             song_file_path)
            call(ffmpeg_command, shell=True)
            song_file_path = outfile_name

        lrc_file_path = lyrics_path_list[0]
        pygame.mixer.music.load(song_file_path)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(NEXT)
        statusbar['text'] = "正在播放" + ' - ' + os.path.basename(song_file_path)
        self.show_details(song_file_path)
        self.show_lrc(lrc_file_path)

    def stop_music(self):
        pygame.mixer.music.set_endevent(STOP)
        for thread in thread_list:
            self.stop_thread(thread)
            thread_list.clear()
        for thread in lrc_thread_list:
            self.stop_thread(thread)
            lrc_thread_list.clear()
        timeformat = '{:02d}:{:02d}'.format(0, 0)
        progress_bar_scale['label'] = timeformat
        currenttimelabel['text'] = timeformat
        lengthlabel['text'] = timeformat
        lrcText.delete(1.0, END)
        pygame.mixer.music.stop()
        statusbar['text'] = "音乐停止"

    def last_music(self):
        global history_dict, str_obj_dict, currentsong, history_index
        if not bool(history_dict) or history_index == 0:
            currentsong = random.choice(list(str_obj_dict.keys()))
        else:
            history_index -= 1
            currentsong = list(history_dict.values())[history_index]
        self.downloadAndPlay()

    def next_music(self):
        global history_dict, str_obj_dict, currentsong, history_index
        if not bool(history_dict) or history_index == (len(history_dict) - 1):
            temp_play_list = list(str_obj_dict.keys())
            if musicMode == 2:
                currentsong = random.choice(temp_play_list)
            else:
                index = get_list_index(temp_play_list, currentsong, -1)
                pre_play_list = temp_play_list[0:index + 1]
                beh_play_list = temp_play_list[index + 1:]
                beh_play_list.extend(pre_play_list)
                play_list = beh_play_list
                currentsong = play_list[0]
            history_index += 1
            history_dict[history_index] = currentsong
        else:
            history_index += 1
            currentsong = list(str_obj_dict.keys())[history_index]
        self.downloadAndPlay()

    def set_vol(self, val):
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)

    def mute_music(self):
        global muted
        if muted:
            pygame.mixer.music.set_volume(0.7)
            volumeBtn.configure(image=volumePhoto)
            scale.set(70)
            muted = FALSE
        else:
            pygame.mixer.music.set_volume(0)
            volumeBtn.configure(image=mutePhoto)
            scale.set(0)
            muted = TRUE

    def change_music_mode(self):
        global musicMode
        if musicMode == 0:
            modeBtn.configure(image=singlePhoto)
            musicMode = 1
        elif musicMode == 1:
            modeBtn.configure(image=randomPhoto)
            musicMode = 2
        else:
            modeBtn.configure(image=orderPhoto)
            musicMode = 0

    def show_details(self, play_song):
        file_data = os.path.splitext(play_song)

        if file_data[1] == '.mp3':
            audio = MP3(play_song)
            total_length = audio.info.length
        else:
            a = pygame.mixer.Sound(play_song)
            total_length = a.get_length()

        mins, secs = divmod(total_length, 60)
        mins = round(mins)
        secs = round(secs)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        lengthlabel['text'] = timeformat


        for thread in thread_list:
            self.stop_thread(thread)
            thread_list.clear()
        count_thread = threading.Thread(target=self.start_count)
        count_thread.setDaemon(True)
        count_thread.start()
        thread_list.append(count_thread)

    def start_count(self):
        global paused, current_time
        # mixer.music.get_busy(): - Returns FALSE when we press the stop button (music stop playing)
        # Continue - Ignores all of the statements below it. We check if music is paused or not.
        current_time = 0
        while True:
            if paused:
                start_time = int(round(time.time() * 1000))
                mins, secs = divmod(current_time, 60)
                mins = round(mins)
                secs = round(secs)
                timeformat = '{:02d}:{:02d}'.format(mins, secs)
                currenttimelabel['text'] = timeformat
                progress_bar_scale['label'] = timeformat
                end_time = int(round(time.time() * 1000))
                time.sleep(abs(1000 - (end_time - start_time)) / 1000)
                # print((1000 - (end_time - start_time) )/1000)
                current_time += 1
            else:
                continue

    def set_prog(self, texts):
        global current_time
        try:
            file_data = os.path.splitext(song_file_path)

            if file_data[1] == '.mp3':
                audio = MP3(song_file_path)
                total_length = audio.info.length
            else:
                a = pygame.mixer.Sound(song_file_path)
                total_length = a.get_length()

            t1 = round(float(texts))
            t2 = total_length / 100
            current_time = t2 * t1
            mins, secs = divmod(current_time, 60)
            mins = round(mins)
            secs = round(secs)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            pygame.mixer.music.play(1, current_time)
            progress_bar_scale['label'] = timeformat
        except Exception as e:
            print(e)

    def on_closing(self):
        self.stop_music()
        root.destroy()

    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop_thread(self, thread):
        self._async_raise(thread.ident, SystemExit)

    def show_lrc(self, lyrics_path):
        listLrc = parseLrc(lyrics_path)
        for thread in lrc_thread_list:
            self.stop_thread(thread)
            lrc_thread_list.clear()
        lrc_thread = threading.Thread(target=self.start_insert, args=(listLrc,))
        lrc_thread.setDaemon(True)
        lrc_thread.start()
        lrc_thread_list.append(lrc_thread)

    def start_insert(self, listLrc):
        global current_time
        lrcText.delete(1.0, END)
        tempTime = 0
        for (key, value) in listLrc:
            if key not in Interval(-1, 4):
                key = key - 1
                if current_time > key:
                    tempTime = key + 1
                    continue
            # print(value)
            while not paused:
                continue
            tempTime = abs(key - tempTime)
            time.sleep(tempTime)
            tempTime = key
            lrcText.insert(END, value + '\r\n')
            lrcText.see(END)
        while True:
            continue


if __name__ == '__main__':
    root = ThemedTk(theme="scidpink", toplevel=True, themebg=True)
    # print(root.get_themes())
    # root.set_theme("arc")

    totalCount = 20

    paused = FALSE
    muted = FALSE
    currentsong = ""
    musicMode = 0
    NEXT = pygame.USEREVENT + 1
    STOP = pygame.USEREVENT + 2

    statusbar = Label(root, text="欢迎来到小尼音乐", relief=SUNKEN, anchor=W, font=('华文行楷', 15, 'italic'))
    statusbar.pack(side=BOTTOM, fill=X)

    # Create the menubar
    menubar = Menu(root)
    root.config(menu=menubar)


    def about_us():
        tkinter.messagebox.showinfo('请求帮助', '需要帮助请联系jiawei.xu！！！')


    def show_admire():
        admire_img = Image.open(os.path.join(os.path.dirname(sys.executable),"static","admire.png"))
        admire_photo = ImageTk.PhotoImage(admire_img)

        admire_lab = Label(image=admire_photo)
        admire_lab.image = admire_photo
        admire_lab.place(x=0, y=0)
        global closeBtn

        def close_admire():
            admire_lab.place_forget()
            closeBtn.destroy()

        closeBtn = ttk.Button(text='返回', command=close_admire)
        closeBtn.place(x=0, y=0, height=70, width=70)


    subMenu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Secret", menu=subMenu)
    subMenu.add_command(label="Help", command=about_us)
    subMenu.add_command(label="Admire", command=show_admire)

    fc = MusicPlayer()
    pygame.init()
    root.title("小尼音乐")
    root.iconbitmap(os.path.join(os.path.dirname(sys.executable),"static","qiaoba.ico"))

    mode_thread = threading.Thread(target=fc.play_mode)
    mode_thread.setDaemon(True)
    mode_thread.start()

    leftframe = Frame(root)
    leftframe.pack(side=LEFT, padx=30, pady=30, ipadx=30, ipady=30)

    v = IntVar()

    entry = Entry(leftframe, font=("宋体", 16, "bold"), fg='black')
    entry.pack(side=TOP, padx=10, pady=10, ipadx=10, ipady=10)
    selectImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","query.png")).resize((40, 40))
    selectPhoto = ImageTk.PhotoImage(selectImage)
    selectBtn = ttk.Button(leftframe, image=selectPhoto, command=fc.selectfile)
    selectBtn.pack(side=TOP, padx=10, pady=15, ipadx=50, ipady=15)

    playlistbox = Listbox(leftframe, selectmode=BROWSE, height=20, width=40)
    playlistbox.pack(side=TOP, padx=20, pady=20)
    xscrollbar = Scrollbar(leftframe, orient=HORIZONTAL, command=playlistbox.xview)
    xscrollbar.pack(side=BOTTOM, fill=X)
    playlistbox.config(xscrollcommand=xscrollbar.set)

    rightframe = Frame(root)
    rightframe.pack(side=RIGHT, padx=30, pady=10, ipadx=30, ipady=5)

    topframe = Frame(rightframe)
    topframe.pack(pady=30, padx=20)

    lengthlabel = Label(topframe, text='00:00', font=('华文行楷', 14, 'italic'))
    lengthlabel.grid(row=1, column=2, padx=10)

    currenttimelabel = Label(topframe, text='00:00', font=('华文行楷', 14, 'italic'))
    currenttimelabel.grid(row=1, column=0, padx=10)

    progress_bar_value = StringVar()
    progress_bar_value.set("0")
    progress_bar_scale = Scale(topframe, from_=0, to=100, orient=HORIZONTAL, length=200, bigincrement=5, digits=17,
                               label='{:02d}:{:02d}'.format(0, 0), variable=progress_bar_value, repeatinterval=100,
                               relief=RAISED,
                               showvalue=False, command=fc.set_prog)
    progress_bar_scale.grid(row=1, column=1, padx=10)

    middleframe = Frame(rightframe)
    middleframe.pack(pady=10, padx=40)

    pauseImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","pause.png")).resize((36, 36))
    pausePhoto = ImageTk.PhotoImage(pauseImage)

    playImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","play.png")).resize((35, 35))
    playPhoto = ImageTk.PhotoImage(playImage)
    playBtn = Button(middleframe, image=playPhoto, command=fc.play_music)
    playBtn.grid(row=0, column=2, padx=20, pady=5)

    stopImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","stop.png")).resize((32, 32))
    stopPhoto = ImageTk.PhotoImage(stopImage)
    stopBtn = Button(middleframe, image=stopPhoto, command=fc.stop_music, height=30, width=30)
    stopBtn.grid(row=0, column=4, padx=20, pady=5)

    lastImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","last.png")).resize((36, 36))
    lastPhoto = ImageTk.PhotoImage(lastImage)
    lastBtn = Button(middleframe, image=lastPhoto, command=fc.last_music, height=30, width=30)
    lastBtn.grid(row=0, column=1, padx=20, pady=5)

    nextImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","next.png")).resize((36, 36))
    nextPhoto = ImageTk.PhotoImage(nextImage)
    nextBtn = Button(middleframe, image=nextPhoto, command=fc.next_music, height=30, width=30)
    nextBtn.grid(row=0, column=3, padx=20, pady=5)

    # 2
    randomImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","random.png")).resize((35, 35))
    randomPhoto = ImageTk.PhotoImage(randomImage)

    # 1
    singleImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","single.png")).resize((35, 35))
    singlePhoto = ImageTk.PhotoImage(singleImage)

    # 0
    orderImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","order.png")).resize((35, 35))
    orderPhoto = ImageTk.PhotoImage(orderImage)
    modeBtn = Button(middleframe, image=orderPhoto, command=fc.change_music_mode)
    modeBtn.grid(row=0, column=0, padx=20, pady=5)

    bottomframe = Frame(rightframe)
    bottomframe.pack(pady=10, padx=40)

    muteImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","mute.png")).resize((35, 35))
    mutePhoto = ImageTk.PhotoImage(muteImage)

    volumeImage = Image.open(os.path.join(os.path.dirname(sys.executable),"static","volume.png")).resize((35, 35))
    volumePhoto = ImageTk.PhotoImage(volumeImage)
    volumeBtn = Button(bottomframe, image=volumePhoto, command=fc.mute_music)
    volumeBtn.grid(row=0, column=1, pady=15, padx=30)

    scale = ttk.Scale(bottomframe, from_=0, to=100, orient=HORIZONTAL, command=fc.set_vol)
    scale.set(70)  # implement the default value of scale when music player starts
    pygame.mixer.music.set_volume(0.7)
    scale.grid(row=0, column=2, pady=15, padx=30)

    lrcframe = Frame(rightframe)
    lrcframe.pack(pady=10, padx=10, ipadx=10, ipady=10)

    lrcText = Text(lrcframe, height=19, width=30, font=('正楷', 14, 'italic'), bg='gray', fg='white')
    lrcText.pack(pady=5, padx=5, ipadx=5, ipady=5)

    root.protocol("WM_DELETE_WINDOW", fc.on_closing)
    root.mainloop()

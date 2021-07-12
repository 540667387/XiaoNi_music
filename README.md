# 小尼音乐

爬取qq音乐，网易云音乐，咪咕音乐三大平台歌曲，并利用某种算法进行去重和排序，基本上可以展示出用户想要的歌曲清单。exe需要配合在static目录文件下使用，因为每次爬取都是全量爬取，所以速度会很慢，后续思考如何改进。



GUI使用的是Tkinter，后续会使用pyQt5进行美化。

# 如何使用
自行下载对应的依赖包，在运行的py文件同级目录中下载一个ffmpeg.exe用于m4a转化成MP3格式

想要运行py文件来启动的话执行music_player_1_5_dev.py
想要运行exe文件来启动的话需要执行pyinstaller -F -i  static/qiaoba.ico music_player_1_5.py --noconsole --hidden-import=addons.migu  --hidden-import=addons.netease --hidden-import=addons.qq
打成exe文件就可以运行了，记得exe文件要与static目录在同一级目录下


后续会改进成客户端服务端模式，可以添加喜欢的歌曲到自己的歌单

### **有想法的一起做做！！！**

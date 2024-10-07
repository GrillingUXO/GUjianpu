* 新增midi导出，自定义旋律容许阈值&音程容差，以及更适合处理总谱/简单旋律的根音分离脚本。

基于music21库和musicpy库的五线谱-简谱转换脚本。这个粗糙的小工具可以将多声部乐谱转换成单声部的乐谱，同时较完整地保留主旋律。

十分感谢 @Rainbow-Dreamer 的musicpy工具包 😍

1：下载 .midi，如果文件是 .musicxml 格式的可以在MuseScore里转换。
<img width="1280" alt="Screen Shot 2024-10-04 at 1 49 11 PM" src="https://github.com/user-attachments/assets/396f108c-b131-426d-bcb3-3c4bf6aa7527">

2：运行脚本。这时会弹出一个 tkinter 文件对话框用于选择要转换的 .midi 文件。脚本会用musicpy库的 split_melody 函数将旋律音从和弦中摘离，并将这些 Piece 对象转换为简谱。
<img width="1280" alt="Screen Shot 2024-10-04 at 1 50 26 PM" src="https://github.com/user-attachments/assets/f507f4a8-4773-4106-840b-9769ded76993">

3：选择下载地址和命名。
<img width="319" alt="Screen Shot 2024-10-04 at 1 52 04 PM" src="https://github.com/user-attachments/assets/cc72a67e-13d7-410a-96f4-666260119f69">

4：简谱文件会以文本格式导出。注意，简谱的时值有时会存在错误（比较经典的是附点八分识别成四分），且休止符无法正常打印。👉👈
<img width="1280" alt="Screen Shot 2024-10-04 at 1 53 14 PM" src="https://github.com/user-attachments/assets/4020148b-28d0-4547-b658-09495176a517">


请确保你已安装 Python 3.x，安装后请通过以下命令安装环境依赖：
```bash
pip3 install -r requirements.txt

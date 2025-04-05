import os
import UnityPy
output_file = "/home/simooo/work/game_loc_translate/outputAssets/resources.assets"
input_file=  "/home/simooo/work/game_loc_translate/srcAssets/resources.assets"
new_font_path = "/home/simooo/work/game_loc_translate/srcAssets/MiSans VF.ttf"
# env = UnityPy.load("resources.assets")

# 读取新的字体数据（二进制方式读取）
with open(new_font_path, "rb") as f:
    new_font_data = f.read()

# 加载 assets 文件
env = UnityPy.load(input_file)

# 遍历所有的对象，查找 Font 类型的对象
for obj in env.objects:
    if obj.type.name == "Font":
        font_obj = obj.read()
        if not font_obj.m_Name == "LiberationSans":
            continue
        # 打印当前字体名称，便于调试
        print(f"替换字体: {font_obj.m_Name}")
        # 如果原字体数据存在，可以根据需要判断字体类型（例如 OTTO 开头代表 OTF 字体）
        # 这里直接替换为新的字体数据
        font_obj.m_FontData = new_font_data
        # 将修改保存到对象中
        font_obj.save()

# 将修改后的 assets 保存到新的文件中
with open(output_file, "wb") as f:
    f.write(env.file.save())

print("字体替换完成！")
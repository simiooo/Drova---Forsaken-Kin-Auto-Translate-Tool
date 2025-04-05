import os
import argparse
import UnityPy

def replace_font(input_file, output_file, new_font_path, target_font_name="LiberationSans"):
    # 读取新的字体数据（二进制方式读取）
    with open(new_font_path, "rb") as f:
        new_font_data = f.read()

    # 加载 assets 文件
    env = UnityPy.load(input_file)

    # 遍历所有的对象，查找 Font 类型的对象
    for obj in env.objects:
        if obj.type.name == "Font":
            font_obj = obj.read()
            if font_obj.m_Name != target_font_name:
                continue
            print(f"替换字体: {font_obj.m_Name}")
            font_obj.m_FontData = new_font_data
            font_obj.save()

    # 将修改后的 assets 保存到新的文件中
    with open(output_file, "wb") as f:
        f.write(env.file.save())

    print("字体替换完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="替换Unity资源文件中的字体")
    parser.add_argument("--input", "-i", required=True, help="输入的资源文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出的资源文件路径")
    parser.add_argument("--font", "-f", required=True, help="新的字体文件路径")
    parser.add_argument("--name", "-n", default="LiberationSans", help="要替换的字体名称（默认是 LiberationSans）")

    args = parser.parse_args()

    replace_font(args.input, args.output, args.font, args.name)

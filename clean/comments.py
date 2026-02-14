import shutil
import subprocess
import tempfile
import argparse
import re
from pathlib import Path


def remove_excessive_newlines(file_path):
    """
    将连续的多个空行压缩为一个空行。
    原理：将 3 个或以上的 \n 替换为 2 个 \n。
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        # 正则说明：\n{3,} 匹配三个及以上的换行符
        # 替换为 \n\n，即保留一个可见的空行
        cleaned_content = re.sub(r'\n{3,}', '\n\n', content)

        # 去除文件末尾多余的换行
        cleaned_content = cleaned_content.strip() + '\n'

        file_path.write_text(cleaned_content, encoding='utf-8')
        print(f"🧹 已清理连续空行")
    except Exception as e:
        print(f"⚠️ 清理空行时出错: {e}")


def clean_single_tex(input_path, output_path=None, skip_newlines=False):
    input_file = Path(input_path).resolve()

    if not input_file.exists() or input_file.suffix != '.tex':
        print(f"❌ 错误: 找不到文件或格式错误 -> {input_path}")
        return

    # 确定输出路径
    if not output_path:
        output_file = input_file.parent / f"{input_file.stem}_cleaned.tex"
    else:
        output_file = Path(output_path).resolve()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        to_clean_dir = tmp_path / "to_clean"
        to_clean_dir.mkdir()

        # 1. 拷贝
        shutil.copy(input_file, to_clean_dir / input_file.name)

        print(f"🚀 正在运行 arxiv_latex_cleaner...")
        try:
            # 2. 运行 arXiv cleaner (处理注释、环境等)
            subprocess.run(["arxiv_latex_cleaner",
                            str(to_clean_dir)],
                           check=True,
                           capture_output=True,
                           text=True)

            cleaned_tex = tmp_path / "to_clean_arXiv" / input_file.name

            if cleaned_tex.exists():
                # 3. 将结果移出到最终位置
                shutil.copy(cleaned_tex, output_file)

                # 4. 可选：进一步清理连续空行
                if not skip_newlines:
                    remove_excessive_newlines(output_file)

                print(f"✅ 处理完成！保存至: {output_file}")
            else:
                print("⚠️ 未找到清理后的生成文件。")

        except subprocess.CalledProcessError as e:
            print(f"❌ 运行失败: {e.stderr}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="单文件 arXiv LaTeX 清理工具")
    parser.add_argument("input", help="输入的 .tex 文件")
    parser.add_argument("-o", "--output", help="指定输出文件名")
    # 增加 --keep-newlines 参数，如果不加则默认执行删除空行
    parser.add_argument("--keep-newlines",
                        action="store_true",
                        help="保留连续的空行（默认会自动压缩）")

    args = parser.parse_args()

    # 依次调用逻辑
    clean_single_tex(args.input, args.output, skip_newlines=args.keep_newlines)

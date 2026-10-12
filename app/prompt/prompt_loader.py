from pathlib import Path


# 加载提示词文件的函数
def load_prompt(name: str) -> str:
    path = Path(__file__).parents[2] / 'prompts' / f'{name}.prompt'
    return path.read_text(encoding='utf-8')


if __name__ == '__main__':
    print(load_prompt('extend_keywords_for_column_recall'))

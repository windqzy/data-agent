# 文件的路径
from pathlib import Path
import yaml
from attr import dataclass
from omegaconf import OmegaConf


def load_by_yaml():
    """
    文件路径（Path 对象）
       │
       ├── 知道文件在哪里
       ├── 可以拼接目录
       ├── 可以获取父目录
       └── 但不代表已经读取了文件

    / 在 Path 对象后面是路径拼接运算符
    """
    # 当前文件的路径 Path(__file__)
    # 住址不是房子本身，文件路径也不是文件内容。
    yaml_path = Path(__file__).parents[0]
    print(yaml_path)
    yaml_path = Path(__file__).parents[1]
    print(yaml_path)
    yaml_path = Path(__file__).parents[2]
    print(yaml_path)
    # 找到文件的路径
    yaml_path = Path(__file__).parents[2] / 'conf' / 'test_config.yaml'
    print(yaml_path)

    #返回文件对象
    with open(yaml_path) as f:
        #读取数据
        obj = yaml.safe_load(f)
        print(obj,type(obj))
        print(obj['name'])

    """
    Python 程序
        │
        │ open(path)
        ▼
    操作系统
        │
        ├── 查找文件
        ├── 检查权限
        ├── 分配文件描述符
        └── 建立文件访问状态
                   │
                   ▼
           Python 文件对象 f
                   │
                   │ f.read()
                   ▼
           读取、解码文件内容
                   │
                   ▼
              Python str
    """


#定义数据类型 等价于__init()__
@dataclass
class PersonConfig():
    name: str
    age: int
    height: float

def load_by_omegaconf():
    # 找到文件的路径
    yaml_path = Path(__file__).parents[2] / 'conf' / 'test_config.yaml'
    print(yaml_path)

    # 返回文件对象
    yaml_data = OmegaConf.load(yaml_path)
    print(yaml_data,type(yaml_data))
    print(yaml_data['name'])
    print(yaml_data.name)

    #将yaml数据转换为制定对象
    person_config:PersonConfig = OmegaConf.to_object(OmegaConf.merge(PersonConfig, yaml_data))
    print(person_config,type(person_config))
    print(person_config.name)
if __name__ == '__main__':
    # load_by_yaml()
    load_by_omegaconf()
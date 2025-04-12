# WebSpider
项目灵感来源于 [阅读APP](https://github.com/gedoor/legado/tree/3.25)，通读了核心源码后，使用Python实现了类似的基于BeautifulSoup的网页解析器和URL解析器。

# URL解析器



# 网页解析器

## 用法

```python
from analysis.analyze_rule import AnalyzeRule
result = AnalyzeRule.get_elements("<div><a>Lab 1</a><a style='dis'>Lab 2</a></div>", "[ {{ @tag[a] @replace[L,0] }} ]")
>>> ['[ 0ab 1 ]', '[ 0ab 2 ]']
```

## 网页解析器

### base 通用指令

- 文本格式化指令
    
    - **replace** [old_val, new_val]
        
        替换字符串

        `@replace[L,l]`

    - **rinsert** [val]

        在右边插入文本

        `@rinsert[end]`

    - **linsert** [val]

        在左边插入文本

        `@linsert[start]`
    
    - **insert** [val, pos]

        在特定位置插入文本

        `@insert[middle, 3]`

    - **regex** [val, group]

        获取正则指定的匹配组

        `@regex[start(.*)end, 1]`

    - **upper**

        文本转大写

        `@upper`

    - **lower**

        文本转小写

        `@lower`

    - **trim**

        清除前后空白符

        `@trim`

    - **str**

        强制转为 str 类型

        `@str`

    - **md**

        将 html 转换为 markdown 格式

        `@md`

- 逻辑操作指令

    - **and**

        合并两个解析成功的结果

        `@and`

    - **or**

        选择一个解析成功的结果

        `@or`

    - **not**

        排除解析成功的结果

        `@not`

    - **union**

        连接两个解析成功的结果

        `@union`

    - **conti**

        继续完成后续指令

        `@conti`

- 列表操作指令

    - **first**

        获取第一个结果

        `@first`

    - **last**

        获取最后一个结果

        `@last`

    - **one** [st]

        获取 *st* 指定索引的一个结果

        `@one[1]`

    - **slice** [st, ed, step]

        获取 [*st*, *ed*) 范围内的结果，可设置步长

        `@slice[1,5,1]`

    - **series** [pos]

        获取一系列指定索引的结果

        `@series[1,3,4,6]`

    - **reverse**

        结果列表取反

        `@reverse`

- 数据存取指令

    - **put** [data, key]

    - **get** [_data, key]

### Soup 指令

- 元素获取指令

    > 参数之前加上 *~* 可启用正则匹配

    - **class** [val]

        `@class[main]` `@class[~ma*]`

    - **id** [val]

        `@id[main]` `@id[~ma*]`

    - **tag** [val]

        `@tag[a]` `tag[div]`

    - **data** [name, val]

        ```html
        <div data-name="test"></div>
        ```

        `@data[name, test]`

    - **href** [val]

        `@href[https://123.com]`

    - **src** [val]

        `@src[https://123.com/1.png]`

    - **value** [val]

        `@value[test]`

    - **prop** [val]

        `@prop[href]`

    - **text**

        `@text`

    - **eq** [css]

        `@eq[.main]`

    - **ne** [css]

        `@ne[.main]`

    - **self**

        `@self`

    - **css** [val]

        `@css[.main]`

    - **children**

        `@children`


### Jsonp 指令

- 元素获取指令

    - **json** [data, j]


## URL解析器

### option
    
```python

class Option(BaseModel):
    method: str = RequestMethod.GET.value
    headers: Union[dict, str, None] = None
    cookies: Union[dict, str, None] = None
    data: Union[dict, str, None] = None
    retry: int = 0
    browser: bool = False
    browser_js: str = ""
    step_time: int = 0

```


### <js>javascript脚本的代码</js>

在URL中可通过 *#result\d+#* 来获取指定顺序js脚本的值

`https://123#result0#.com/<js>let i = 0; i</js>`
解析后:
`https://1230.com`

### py扩展工具函数

- py.soup

- py.ajax

- py.ua

- py.read_file

- py.urlencode

```
.venv\Scripts\activate //激活venv环境
//实验环境，再deep_gnss原venv环境基础上将pandas版本改为1.x  eg: "pandas==1.3.5",
python import.py  //修改代码中的所有路径  进行mapped_gnssdata.csv输出
python map_coordiantes.py //修改路径  进行ground_truth_updata.csv输出
python timestamp.py  //时间戳匹配  输出derived.csv  ground_truth.csv作为val数据
```


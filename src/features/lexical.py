import math
import re
import numpy as np
import pandas as pd

CHARACTERS = {"sq":"'", "dq":'"', "lt":"<", "gt":">", "lparen":"(", "rparen":")", "semicolon":";",
              "equals":"=", "amp":"&", "pct":"%", "plus":"+", "minus":"-", "star":"*", "slash":"/",
              "pipe":"|", "hash":"#", "quest":"?", "at":"@", "colon":":", "comma":",", "dot":".", "space":" "}
SQL = ["select","union","insert","update","delete","drop","where","from","or","and","exec","order","by",
       "waitfor","delay","cast","table","database","like"]
XSS = ["script","alert","javascript","onerror","onload","document","cookie","src","iframe","style","background","location","eval","prompt"]


def entropy(text):
    if not text: return 0.0
    _, counts = np.unique(list(text), return_counts=True); probabilities = counts / counts.sum()
    return float(-(probabilities * np.log2(probabilities)).sum())


def extract(frame):
    text = frame.text.astype(str).str.lower().reset_index(drop=True)
    result = pd.DataFrame(index=range(len(frame)))
    for name, character in CHARACTERS.items(): result["char_" + name] = text.str.count(re.escape(character))
    for word in SQL: result["sql_" + word] = text.str.count(rf"\b{word}\b")
    result["sql_comment_dash"] = text.str.count(r"--")
    result["sql_comment_block"] = text.str.count(r"/\*") + text.str.count(r"\*/")
    for word in XSS: result["xss_" + word] = text.str.count(rf"\b{word}\b")
    result["len_total"] = text.str.len()
    result["path_depth"] = frame.url.astype(str).reset_index(drop=True).str.count("/")
    length = result.len_total.replace(0, 1)
    result["ratio_digits"] = text.str.count(r"\d") / length
    result["ratio_nonalnum"] = text.str.count(r"[^a-z0-9]") / length
    result["enc_pct"] = (frame.url.astype(str).reset_index(drop=True) + " " + frame.body.astype(str).reset_index(drop=True)).str.count(r"%[0-9a-fA-F]{2}")
    result["path_traversal"] = text.str.count(r"\.\./")
    result["entropy"] = text.map(entropy)
    return result.astype("float32")


def feature_set(matrix, name):
    columns = list(matrix.columns)
    sql = [value for value in columns if value.startswith("sql_")]
    chars = [value for value in columns if value.startswith("char_")]
    if name == "lex64": return matrix
    if name == "sql21": return matrix[sql]
    if name == "no_encoding": return matrix.drop(columns=["char_pct", "enc_pct"])
    if name == "no_sql_keywords": return matrix.drop(columns=sql)
    if name == "no_length": return matrix.drop(columns=["len_total", "path_depth"])
    if name == "no_special_chars": return matrix.drop(columns=chars)
    if name == "char_rates":
        length = matrix.len_total.clip(lower=1)
        return matrix[chars].div(length, axis=0).rename(columns=lambda x: "rate_" + x)
    raise ValueError(name)

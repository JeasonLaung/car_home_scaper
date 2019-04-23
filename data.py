import re
string = 'asfavsdfzasfasfas'
pattern = '停售'
print(re.compile(pattern=pattern).findall(string))
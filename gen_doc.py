from BeautffulSoup import BeautifulSoup
from markdown import markdown
README = 'README.md'

mdtext = open(README, 'r').read()

html = markdown(mdtext)
text = ''.join(BeautifulSoup(html).findAll(text=True))

print(text)
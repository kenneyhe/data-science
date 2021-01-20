# data-science
juypter notebooks for backing up to private docker registry


## requirements

```bash
  brew install pre-commit
  export PATH=$PATH:/usr/local/Cellar/pre-commit/2.9.3/bin

  brew install git-secrets
  git secrets --add 'AWS_SECRET_ACCESS_KEY\s*=\s*.+'
  git secrets --add 'password\s*=\s*.+'
  git secrets --add --allowed --literal '******'
  export AWS_SECRET_ACCESS_KEY=*******
  export password=******
  

```

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kenneyhe/data-science.git/HEAD)

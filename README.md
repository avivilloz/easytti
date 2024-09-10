# PKG

<SHORT-PKG-DESCRIPTION>

## Description:

<LONG-PKG-DESCRIPTION>

## How to install:

Run the following command in your python venv:

```
pip install git+https://github.com/avivilloz/<PKG-NAME>.git@main#egg=<PKG-NAME>
```

Or add the following line to your project's `requirement.txt` file:

```
git+https://github.com/avivilloz/<PKG-NAME>.git@main#egg=<PKG-NAME>
```

And run the following command:

```
pip install -r requirements.txt
```

## How to use:

`file.py`
```
from <PKG-NAME> import <PKG-FUNCTION>

# Use <PKG-FUNCTION>
```
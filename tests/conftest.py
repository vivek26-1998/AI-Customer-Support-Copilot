"""Keep deterministic tests independent of local credentials and dotenv files."""
import os

os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ.pop('OPENAI_API_KEY', None)
os.environ['OPENAI_AGENTS_DISABLE_TRACING'] = '1'

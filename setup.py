from setuptools import setup
from os import path
base_dir = path.abspath(path.dirname(__file__))
setup(
  name = 'xtempmail',        
  packages = ['xtempmail'],
  include_package_data=True,
  long_description=open(path.join(base_dir, "README.md"), encoding="utf-8").read(),
  long_description_content_type='text/markdown',
  version = '0.1',    
  license='MIT',     
  description = 'Temporary Email', 
  author = 'Krypton Byte',                  
  author_email = 'galaxyvplus6434@gmail.com',     
  url = 'https://github.com/krypton-byte/xtempmail',      
  keywords = ['temporary','mail','email','autoreply'], 
  install_requires=[           
          'requests',
          'Rx'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      
    'Intended Audience :: Developers',      
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',  
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)
FROM python:3.8

COPY src/ /

RUN pip install -r requirements.txt
    chmod +x /usr/local/lib/python3.8/site-packages/data_minimization_tools/cvdi/bin/cv_di
    chmod +x /usr/local/lib/python3.8/site-packages/data_minimization_tools/cvdi/bin/cv_di.exe



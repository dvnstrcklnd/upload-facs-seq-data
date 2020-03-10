FROM jupyter/scipy-notebook as notebook-base

RUN pip install pydent \
  && pip install agavepy==1.0.0a4

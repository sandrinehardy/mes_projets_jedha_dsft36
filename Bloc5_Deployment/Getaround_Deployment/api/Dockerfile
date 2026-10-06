FROM continuumio/miniconda3

RUN apt-get update -y

# Spécifique à Hugging Face : on crée un utilisateur "user" (ID 1000) et on travaille avec lui
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY requirements.txt /dependencies/requirements.txt
RUN pip install -r /dependencies/requirements.txt

COPY --chown=user . $HOME/app

# Le modèle est entraîné pendant la construction de l'image
RUN python train.py

CMD fastapi run app.py --port 7860

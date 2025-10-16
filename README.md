# POC_HoneyPot

Petit honeypot écrit en Python.

## Présentation

Ce projet est un proof-of-concept (POC) de honeypot simple, développé en Python.  
Il est destiné à être lancé via Docker et à être protégé en frontal par un serveur Nginx.

---

## Lancement rapide

### Prérequis

- [Docker](https://www.docker.com/) installé sur votre machine.
- [Nginx pour Windows](https://nginx.org/en/download.html) installé et lancé.
- Windows comme système d'exploitation (pour l'exemple de configuration fourni).

---

### 1. Lancer le honeypot avec Docker

Dans le dossier du projet, ouvrez un terminal et exécutez :

```sh
docker compose up -d
```

Cela va démarrer l’application Flask du honeypot sur le port 8081 de l’hôte.

---

### 2. Installer et configurer Nginx sur Windows

1. **Téléchargez** la version Windows de Nginx sur [nginx.org/en/download.html](https://nginx.org/en/download.html)  
   Décompressez l’archive où vous le souhaitez.

2. **Remplacez** la configuration par défaut dans le fichier `nginx.conf` (généralement dans le dossier `conf`) par la configuration suivante :

    ```nginx
    worker_processes  1;
    events { worker_connections 1024; }

    http {
        include       mime.types;
        default_type  application/octet-stream;
        sendfile        on;
        keepalive_timeout  65;

        server {
            listen 8080;
            server_name _;

            # Buffering off pour réduire latence d'écriture
            proxy_buffering off;

            location / {
                # Backend Flask exposé par docker-compose sur l'hôte à 127.0.0.1:8081
                proxy_pass http://127.0.0.1:8081;

                # Forward headers so that Flask (ProxyFix) can pick the real IP
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;

                # timeouts (optionnel)
                proxy_connect_timeout 5s;
                proxy_send_timeout 60s;
                proxy_read_timeout 60s;
            }
        }
    }
    ```

3. **Démarrez** Nginx en exécutant `nginx.exe` (dans le dossier où vous avez extrait Nginx).

---

### 3. Accès au honeypot

Le honeypot sera alors accessible via [http://localhost:8080](http://localhost:8080).

---

## Remarques

- Nginx reçoit les connexions sur le port 8080 et les reverse-proxy vers le honeypot Flask exposé sur le port 8081.
- Cette configuration est destinée à un environnement de test/Démo sous Windows.
- Pour une utilisation réelle, pensez à renforcer la sécurité et adapter la configuration à vos besoins.

---

## Licence

MIT

## Tools and installation

Install Docker (for linux):

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt install docker-ce
sudo systemctl status docker
sudo usermod -aG docker ${USER}
su - ${USER}
```

Or install Docker Desktop: [Installation instruction](https://docs.docker.com/desktop/install/windows-install/)

Copy and paste values of .env.example file to .env file and edit it for your purposes:

```bash
cat .env_template > .env
```

## Run

Start application:

```bash
docker compose up -d
```
```

## Migrations

After any changes in models create and apply migrations:

```bash
docker exec free_vpn  python manage.py makemigrations
docker exec free_vpn  python manage.py migrate
```
Install chrome:
```bash
sudo apt install wget unzip gnupg
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
sduo apt update
sudo apt install google-chrome-stable
``` 

Or install from here: [Download chrome](https://www.google.com/intl/uk_ua/chrome/) 

Sync dependencies:

```bash
pipenv sync
```

Run important inventory :

```bash
docker compose -f inventory-compose.yml up -d
```

Sync migrations:

```bash
pipenv run python manage.py migrate
```

Collect static filest to static/ directory:

```bash
pipenv run python manage.py  collectstatic
```

Create super user (Account with unlimited rights on admin panel):

```bash
pipenv run python manage.py  createsuperuser
```

Run app for development purposes:

```bash
pipenv run python manage.py runserver 8005
```


After any changes in models create and apply migrations:

```bash
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
```

## Additional commands

Delete all containers and flash all trash:

```bash
docker stop $(docker ps -aq) && docker rm $(docker ps -aq) && docker container prune -f
```

Delete all images:

```bash
docker image rm $(docker image ls -q) && docker image prune -af
```

## Testing

Recomended sites for testing proxy:
- [QA theory](https://the-internet.herokuapp.com/)

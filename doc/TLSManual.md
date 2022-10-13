# ����ԃf�[�^�A�g���: TLS���ݔF�ؐݒ��
- ���p�҃R�l�N�^-�񋟎҃R�l�N�^�Ԃ̒ʐM�ɂ����Ă�TLS�ɂ�鑊�ݔF�؂��s�����Ƃ��O��ƂȂ�A  
���p�ҋy�ђ񋟎҂ɂď���������̂ƂȂ�B
- �{�y�[�W�ł̓T���v���Ƃ��ė��p�҃R�l�N�^-�񋟎҃R�l�N�^�Ԃɂ�����TLS���ݔF�؂��������邽�߂̐ݒ����L�ڂ���B
- TLS���ݔF�؂͉��}�̃v���L�V�y�у��o�[�X�v���L�V�ɂĎ�������B
![Alt text](../doc/png/conf_example.png?raw=true "Title")

## �O�����

- �{�y�[�W�ŃT���v���Ƃ��Č��J����OSS�y�ѓ���m�F�ς݂̃o�[�W�����͈ȉ��̒ʂ�
    - �v���L�V�FSquid 4.10
    - ���o�[�X�v���L�V�FNginx 1.19.2

- �v���L�V����у��o�[�X�v���V�L�̓R�l�N�^�Ɋ܂܂��
    - �v���L�V�F���p�҃R�l�N�^(connector/src/consumer/squid)
    - ���o�[�X�v���L�V�F�񋟎҃R�l�N�^(connector/src/provider/nginx)

- TLS���ݔF�؂ɕK�v�ȏؖ����A�閧��(pem�`��)�̓��[�U�[�ɂĎ��O�ɏ����ς݂ł��邱�Ƃ�O��Ƃ���B
  - �e���ŕK�v�ȃt�@�C���͈ȉ��̒ʂ�
    - ���p�ґ��F�N���C�A���g�ؖ����A�閧��(�Í����Ȃ�)
    - �񋟎ґ��F�T�[�o�[�ؖ����A�閧���A�N���C�A���g�F�ؐݒ�pCA�ؖ���

- Linux ��ł̓����O��Ƃ���B
  - Docker�ADocker Compose �����O�C���X�g�[������Ă��邱�Ƃ�O��Ƃ���B
  - �Ή����� Docker Version �͈ȉ��̒ʂ�Ƃ���B
    - Docker 20.10.1
  - �Ή����� OS �́ALinux �̏�L Docker ���T�|�[�g���� OS �Ƃ���B

- �{�y�[�W�ł�TLS���ݔF�؂ɕK�v�Ȑݒ�l�݂̂̋L�ڂƂȂ�B
  - TLS�F�؈ȊO�̓���Ɋւ��ݒ�ɂ��Ă͕K�v�ɉ����ă��[�U�[���ōl�����邱�ƁB

# ���p�Ҋ��v���L�V�ݒ�

## �v���L�V(Squid)�\�z�菇

1. �R���t�B�O�t�@�C���̐ݒ�A�t�@�C���z�u

SSL Bump�ݒ�p���ȏ���SSL�ؖ������쐬
```
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout squidCA.pem -out squidCA.pem
```
���ؖ����̗L��������365���ŉ��u�����Ă��邽�߁A�K�v�ɉ����Ċ�����ݒ肷�邱�ƁB

SSL Bump�ݒ�p���ȏ���SSL�ؖ����A�N���C�A���g�ؖ����A�閧�������L�f�B���N�g���ɔz�u
```
connector/src/consumer/squid/volumes/ssl/
```


- squid.conf
  <br>connector/src/consumer/squid/volumes�ɔz�u<br>

  | �ݒ�p�����[�^ | �T�v |
  | :------------- | :-------------------------- |
  | http_port | ssl_bump��ݒ�B |
  | tls_outgoing_options | �T�[�o�[�ڑ����Ɏg�p����N���C�A���g�ؖ����A�閧����ݒ� |

 - �ݒ��
```
http_port 3128 ssl-bump generate-host-certificates=on dynamic_cert_mem_cache_size=4MB cert=/etc/squid/ssl/squidCA.pem
tls_outgoing_options cert=/etc/squid/ssl/{�N���C�A���g�ؖ���} key=/etc/squid/ssl/{�N���C�A���g�閧��}
```
�N���C�A���g�ؖ����A�閧���̓��[�U�[�ŏ��������t�@�C�����ɒu��������B

3. ����v���L�V(Squid)�N��

```
cd connector/src/consumer/squid
docker-compose -f docker-compose_initial.yml up -d --build
```

4. ����v���L�V(Squid)�N���m�F

```
docker-compose ps
    Name                Command           State           Ports
------------------------------------------------------------------------
forward-proxy   /usr/sbin/squid -NYCd 1   Up      0.0.0.0:3128->3128/tcp
```

5. ����v���L�V(Squid)TLS�ݒ�

```
docker exec -it forward-proxy /usr/lib/squid/security_file_certgen -c -s /var/lib/squid/ssl_db -M 20MB
docker cp forward-proxy:/var/lib/squid/ssl_db ./volumes/
docker-compose -f docker-compose_initial.yml stop
```
## �v���L�V(Squid)�N���菇
[����ԃf�[�^�A�g���](README.md "���p�҃R�l�N�^�N���菇")  �Q�ƁB

## �v���L�V(Squid)��~�菇
[����ԃf�[�^�A�g���](README.md "���p�҃R�l�N�^��~�菇")  �Q�ƁB


# �񋟎Ҋ����o�[�X�v���L�V�ݒ�

## ���o�[�X�v���L�V(nginx)�\�z�菇

1. �R���t�B�O�t�@�C���̐ݒ�A�t�@�C���z�u

�T�[�o�[�ؖ����A�閧���A�N���C�A���g�F�ؗpCA�ؖ��������L�f�B���N�g���ɔz�u
```
connector/src/provider/nginx/volumes/ssl/
```


- default.conf
  <br>connector/src/provider/nginx/volumes/�ɔz�u<br>

  | �ݒ�p�����[�^ | �T�v |
  | :------------- | :-------------------------- |
  | ssl_certificate | �T�[�o�[�ؖ�����ݒ� |
  | ssl_certificate_key | �閧���t�@�C����ݒ� |
  | ssl_verify_client | �N���C�A���g�F�؎g�p���ɐݒ�(�ݒ�l:on) |
  | ssl_client_certificate | �N���C�A���g�F�؂Ɏg�p����CA�ؖ�����ݒ� |
  | location /cadde/api/v1/file | proxy_pass�ɒ񋟎҃R�l�N�^�̃J�^���O����IF���w�� |
  | location /api/3/action/package_search | proxy_pass�ɒ񋟎҃R�l�N�^�̃f�[�^����IF���w�� |

 - �ݒ��
```
    ssl_certificate /etc/nginx/ssl/{�T�[�o�[�ؖ���};
    ssl_certificate_key /etc/nginx/ssl/{�T�[�o�[�閧��};
    ssl_verify_client on;
    ssl_client_certificate /etc/nginx/ssl/{CA�ؖ���};
    location /cadde/api/v1/file {
        proxy_pass http://{�񋟎҃R�l�N�^��FQDN�܂���IP�A�h���X}:38080/cadde/api/v1/file;
    }

    location /api/3/action/package_search {
        proxy_pass http://{�񋟎҃R�l�N�^��FQDN�܂���IP�A�h���X}:28080/api/3/action/package_search;
    }
```
�T�[�o�[�ؖ���,�T�[�o�[�閧��,CA�ؖ����̓��[�U�[�ŗp�ӂ����t�@�C�����ɒu��������B

## ���o�[�X�v���L�V(nginx)�N���菇
[����ԃf�[�^�A�g���](README.md "�񋟎҃R�l�N�^�N���菇 ")  �Q�ƁB

## ���o�[�X�v���L�V(nginx)��~�菇
[����ԃf�[�^�A�g���](README.md "�񋟎҃R�l�N�^��~�菇 ")  �Q�ƁB

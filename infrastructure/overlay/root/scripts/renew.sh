#!/bin/bash
site=$1
email=$2
echo Renew certificate for $site
rm /etc/haproxy/sslexports/$site
certbot certonly --standalone --agree-tos -m $email --no-eff-email -d $site --http-01-port=8888 --force-renewal
pushd /etc/letsencrypt/live/$site/
cat cert.pem chain.pem fullchain.pem privkey.pem >> /etc/haproxy/sslexports/$site
popd

systemctl restart haproxy

FROM ubuntu:20.04

ENV LD_LIBRARY_PATH=/open5gs/install/lib/x86_64-linux-gnu

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y\
        python3-pip python3-setuptools python3-wheel ninja-build \
        build-essential flex bison git libsctp-dev libgnutls28-dev \
        libgcrypt-dev libssl-dev libidn11-dev libmongoc-dev libbson-dev \
        libyaml-dev libnghttp2-dev libmicrohttpd-dev libcurl4-gnutls-dev \
        libtins-dev meson curl ca-certificates netbase ifupdown net-tools \
        iputils-ping iptables tcpdump iperf3 mongodb

# apt install gets deprecated nodejs
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs

RUN update-ca-certificates

# Todo (Malte): Create TUN device here

# Copy local open5gs source and install
ENV CORE_PATH /open5gs
RUN mkdir -p ${CORE_PATH}
COPY open5gs ${CORE_PATH}
WORKDIR ${CORE_PATH}
RUN make install
RUN cd ${CORE_PATH}/webui && npm ci --no-optional

WORKDIR ${CORE_PATH}
CMD ["bash"]

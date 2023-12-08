#!/bin/bash

#fonts color
Green="\033[32m"
Red="\033[31m"
#Yellow="\033[33m"
GreenBG="\033[42;37m"
RedBG="\033[41;37m"
YellowBG="\033[43;37m"
Font="\033[0m"

#notification information
Info="${Green}[信息]${Font}"
OK="${Green}[OK]${Font}"
Error="${Red}[错误]${Font}"
Warning="${Red}[警告]${Font}"


source '/etc/os-release'
VERSION=$(echo "${VERSION}" | awk -F "[()]" '{print $2}')


is_root() {
  if [ 0 == $UID ]; then
    echo -e "${OK} ${GreenBG} 当前用户是root用户，进入安装流程 ${Font}"
    sleep 3
  else
    echo -e "${Error} ${RedBG} 当前用户不是root用户，请切换到root用户后重新执行脚本 ${Font}"
    exit 1
  fi
}

judge() {
  if [[ 0 -eq $? ]]; then
    echo -e "${OK} ${GreenBG} $1 完成 ${Font}"
    sleep 1
  else
    echo -e "${Error} ${RedBG} $1 失败${Font}"
    exit 1
  fi
}

check_system() {
  if [[ "${ID}" == "centos" && ${VERSION_ID} -ge 7 ]]; then
    echo -e "${OK} ${GreenBG} 当前系统为 Centos ${VERSION_ID} ${VERSION} ${Font}"
    INS="yum"
  elif [[ "${ID}" == "debian" && ${VERSION_ID} -ge 8 ]]; then
    echo -e "${OK} ${GreenBG} 当前系统为 Debian ${VERSION_ID} ${VERSION} ${Font}"
    INS="apt"
    $INS update
    ## 添加 Nginx apt源
  elif [[ "${ID}" == "ubuntu" && $(echo "${VERSION_ID}" | cut -d '.' -f1) -ge 16 ]]; then
    echo -e "${OK} ${GreenBG} 当前系统为 Ubuntu ${VERSION_ID} ${UBUNTU_CODENAME} ${Font}"
    INS="apt"
    rm /var/lib/dpkg/lock
    dpkg --configure -a
    rm /var/lib/apt/lists/lock
    rm /var/cache/apt/archives/lock
    $INS update
  else
    echo -e "${Error} ${RedBG} 当前系统为 ${ID} ${VERSION_ID} 不在支持的系统列表内，安装中断 ${Font}"
    exit 1
  fi

  $INS install dbus -y

  systemctl stop firewalld
  systemctl disable firewalld
  echo -e "${OK} ${GreenBG} firewalld 已关闭 ${Font}"

  systemctl stop ufw
  systemctl disable ufw
  echo -e "${OK} ${GreenBG} ufw 已关闭 ${Font}"
}

config_chrony() {
    if [[ "${ID}" == "centos" && ${VERSION_ID} -ge 7 ]]; then
      echo -e "${OK} ${GreenBG} 当前系统为 Centos ${VERSION_ID} ${VERSION} ${Font}"
      INS="yum"
      systemctl start chronyd
      judge "启动时间同步服务器"

      systemctl enable chronyd
      judge "启动开机自启时间同步服务器"

    elif [[ "${ID}" == "debian" && ${VERSION_ID} -ge 8 ]]; then
      echo -e "${OK} ${GreenBG} 当前系统为 Debian ${VERSION_ID} ${VERSION} ${Font}"
      INS="apt"
      $INS update
      ## 添加 Nginx apt源
    elif [[ "${ID}" == "ubuntu" && $(echo "${VERSION_ID}" | cut -d '.' -f1) -ge 16 ]]; then
      echo -e "${OK} ${GreenBG} 当前系统为 Ubuntu ${VERSION_ID} ${UBUNTU_CODENAME} ${Font}"
      INS="apt"
      rm /var/lib/dpkg/lock
      dpkg --configure -a
      rm /var/lib/apt/lists/lock
      rm /var/cache/apt/archives/lock
      $INS update
    else
      echo -e "${Error} ${RedBG} 当前系统为 ${ID} ${VERSION_ID} 不在支持的系统列表内，安装中断 ${Font}"
      exit 1
    fi


}

dependency_install() {
  ${INS} install ca-cert* -y
  judge "更新证书认证中心"

  ${INS} install chrony -y
  judge "安装时间同步服务器"

  config_chrony
  judge "配置时间同步服务器"

  date=`date`
  echo "现在的时间是 ${date}"
  sleep 5

  ${INS} install wget git lsof -y

  ${INS} -y install bc
  judge "安装 bc"

  ${INS} -y install unzip
  judge "安装 unzip"

  ${INS} -y install curl
  judge "安装 curl"

  ${INS} -y install python36
  judge "安装 python36"

  ${INS} -y install python36
  judge "安装 python36"

  ${INS} -y install gcc python3-devel -y
  judge "安装Python依赖"

  mkdir -p /usr/local/bin >/dev/null 2>&1
}

basic_optimization() {
  # 最大文件打开数
  sed -i '/^\*\ *soft\ *nofile\ *[[:digit:]]*/d' /etc/security/limits.conf
  sed -i '/^\*\ *hard\ *nofile\ *[[:digit:]]*/d' /etc/security/limits.conf
  echo '* soft nofile 65536' >>/etc/security/limits.conf
  echo '* hard nofile 65536' >>/etc/security/limits.conf

  ulimit -SHn 10240
  ulimit -SHs unlimited
  echo '500000' > /proc/sys/net/nf_conntrack_max

  # 关闭 Selinux
  if [[ "${ID}" == "centos" ]]; then
    sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
    setenforce 0 && echo -e "${OK} ${Green} 已经关闭selinux ${Font}" || echo -e "${Error} ${RedBG} 关闭selinux出错 ${Font}"
  fi

}

python_requirements() {
  pip3 install -r requirements.txt
  judge "安装python3 依赖"
}

prepare_process(){
  is_root
  check_system
  dependency_install
  basic_optimization
  judge "系统准备"
  python_requirments
  sleep 5
  echo "请执行python 命令执行下一步 "
}

list(){
    case $1 in
    run)
        prepare_process
        ;;
    *)
        echo -e "请使用 ${RedBG} bash $0 run ${Font} 选项，以安装准备运行环境"
        exit 1
        ;;
    esac
}

list "$1"
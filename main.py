# encoding: utf-8
import argparse
from utils.controllerFactory import Xray, get_net_card, is_root
from utils.color import *

xray = Xray()


def uninstall(args):
    xray.uninstall()


def install(args):
    xray.install()


def list_node(args):
    xray.list_node()


if __name__ == '__main__':
    if not is_root():
        print("请使用root运行")
        exit(1)

    parser = argparse.ArgumentParser(description='Mutilation IP Cluster Server Management Script')
    parser.add_argument("--list", '-L', action='store_true', default=False,
                        help="list all nodes in this Cluster server")
    parser.set_defaults(func=list_node)
    subparsers = parser.add_subparsers(help='choose into sub menu')

    parser_a = subparsers.add_parser('install', help='Full Install')
    parser_a.add_argument('--name', type=str, help='Prefix name of the generated node')
    parser_a.add_argument('--mode', type=str, help='Transport Layer Protocol')
    parser_a.set_defaults(func=install)

    parser_uninstall = subparsers.add_parser('uninstall', help='Remove From This Computer')
    parser_uninstall.set_defaults(func=uninstall)

    # parser_s = subparsers.add_parser('modify', help='Edit the name of a node')
    # parser_s.add_argument('--name', type=str, help='NodeName')
    # parser_s.add_argument('--port', type=int, help='Port')
    # parser_s.add_argument('--network', type=str, help='Network')
    # parser_s.add_argument('--path', type=str, help='path')
    # parser_s.set_defaults(func=modify)

    args = parser.parse_args()
    # execute function
    args.func(args)

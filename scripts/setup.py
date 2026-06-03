#!/usr/bin/env python3
"""Interactive setup wizard for Cinema Manager."""

import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "config.example.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    if os.path.exists(EXAMPLE_PATH):
        with open(EXAMPLE_PATH) as f:
            return json.load(f)
    return {
        "quark": {"username": "", "password": "", "cookie": ""},
        "plugins": {"wp365": {"enabled": True}, "mini4k": {"enabled": False}},
        "save_folder": "夸克影视",
        "omdb_api_key": "",
    }


def save_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 配置已保存到 {CONFIG_PATH}")


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val = input(f"{prompt}{hint}: ").strip()
    return val if val else default


def main():
    print("=" * 50)
    print("🎬 Cinema Manager 设置向导")
    print("=" * 50)

    config = load_config()

    # ── Step 1: Quark Auth ──
    print("\n📁 第一步：夸克网盘登录\n")
    print("  方式一：账号密码（推荐，自动刷新）")
    print("  方式二：Cookie（手动，约7天过期）")
    print()

    method = ask("选择登录方式 (1=账号密码, 2=Cookie)", "1")

    if method == "1":
        username = ask("夸克账号（手机号或邮箱）", config["quark"].get("username", ""))
        password = ask("夸克密码", config["quark"].get("password", ""))
        config["quark"]["username"] = username
        config["quark"]["password"] = password
        config["quark"]["cookie"] = ""  # Clear cookie if using account
    else:
        print("\n  获取Cookie：浏览器打开 pan.quark.cn → F12 → Application → Cookies")
        print("  复制所有cookie内容粘贴过来\n")
        cookie = ask("Cookie", config["quark"].get("cookie", ""))
        config["quark"]["cookie"] = cookie
        config["quark"]["username"] = ""
        config["quark"]["password"] = ""

    # ── Step 2: Resource Sites ──
    print("\n🔍 第二步：资源站配置\n")
    print("  wp365 — 免费聚合站，夸克+百度链接，无需注册")
    print("  mini4k — 4K资源站，需付费会员账号")
    print()

    wp365 = ask("启用 wp365？(y/n)", "y")
    config["plugins"]["wp365"]["enabled"] = wp365.lower() == "y"

    mini4k = ask("启用 mini4k？(y/n)", "n")
    if mini4k.lower() == "y":
        config["plugins"]["mini4k"]["enabled"] = True
        config["plugins"]["mini4k"]["username"] = ask("mini4k 账号")
        config["plugins"]["mini4k"]["password"] = ask("mini4k 密码")
    else:
        config["plugins"]["mini4k"]["enabled"] = False

    # ── Step 3: Genre Classification ──
    print("\n🎭 第三步：自动类型分类\n")
    print("  影片会自动归入 动作/剧情/科幻 等文件夹")
    print()
    print("  推荐：OMDB API（免费，1000次/天，准确率高）")
    print("  备选：从资源站页面抓取（免费，无需注册，准确率一般）")
    print("  关闭：不分类，所有影片放在一个目录下")
    print()

    genre_choice = ask("选择分类方式 (1=OMDB推荐, 2=仅资源站抓取, 3=不分类)", "1")

    if genre_choice == "1":
        print("\n  获取OMDB Key：")
        print("  1. 打开 http://www.omdbapi.com/apikey.aspx")
        print("  2. 选择 FREE，填写邮箱")
        print("  3. 收到邮件，复制 API Key")
        print()
        omdb_key = ask("OMDB API Key")
        config["omdb_api_key"] = omdb_key
    elif genre_choice == "2":
        config["omdb_api_key"] = ""
        print("  → 将从资源站页面抓取类型信息（mini4k效果最好）")
    else:
        config["omdb_api_key"] = ""
        print("  → 不自动分类，所有影片放在 save_folder 根目录")

    # ── Step 4: Save Folder ──
    print("\n📂 第四步：保存目录\n")
    folder = ask("夸克网盘中的保存目录名", config.get("save_folder", "夸克影视"))
    config["save_folder"] = folder

    # ── Save ──
    save_config(config)

    # ── Summary ──
    print("\n" + "=" * 50)
    print("📋 配置摘要")
    print("=" * 50)
    if config["quark"].get("username"):
        print(f"  夸克登录：账号 {config['quark']['username']}")
    elif config["quark"].get("cookie"):
        print(f"  夸克登录：Cookie（{len(config['quark']['cookie'])}字符）")
    else:
        print("  ⚠️  夸克未配置！")

    enabled = [k for k, v in config["plugins"].items() if v.get("enabled")]
    print(f"  资源站：{', '.join(enabled) if enabled else '无'}")
    print(f"  保存目录：{config['save_folder']}")

    if config.get("omdb_api_key"):
        print(f"  类型分类：OMDB API ✅")
    elif genre_choice == "2":
        print(f"  类型分类：资源站抓取")
    else:
        print(f"  类型分类：关闭")

    print("\n🎬 完成！对你的 Hermes Agent 说「我要看电影」试试吧！\n")


if __name__ == "__main__":
    main()

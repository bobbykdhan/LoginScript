# Schedule I dedicated server for Linux

This folder sets up and runs a 24/7 **Schedule I** dedicated server on a Linux PC.

Schedule I has no official dedicated server and no native Linux build. This
toolkit uses the community mod
[S1DedicatedServers](https://github.com/ifBars/S1DedicatedServers) (S1DS, GPL-3.0).
It runs the Windows game headless under **Wine**, with **MelonLoader** loading
the mod. The steps match the mod's official Docker image. The `s1ds` script
automates install, updates, a systemd service, the server console, backups and
save imports.

> S1DS is a community project. TVGS, the developer of Schedule I, does not make
> or support it. Schedule I patches can break the mod until S1DS releases an
> update. Run `s1ds update` after S1DS publishes a new release.

## What you need

- A 64-bit Linux PC: Ubuntu/Debian, Fedora, Arch or openSUSE. **A headless
  server works fine (e.g. Ubuntu Server over SSH).** No desktop or monitor is
  needed: the game runs on a virtual display (Xvfb).
- At least 2 CPU cores, 4 GB of free RAM and about 10 GB of free disk. 4 cores
  and 8 GB are better for several players. The server runs the whole game,
  headless, under Wine.
- A Steam account that **owns Schedule I**. SteamCMD uses it once to download
  the game files. The server itself logs in to Steam anonymously, so you can
  keep playing on the same account.
- Wine 9 or newer. `s1ds deps` installs it. Where the distro only packages an
  older Wine (e.g. Ubuntu 22.04, Debian 12), it adds the official WineHQ
  repository automatically. `s1ds deps --winehq` forces WineHQ's current stable
  Wine (11), the same version the mod's Docker image uses.
- A normal (non-root) user to run the server. Wine does not work properly as
  root, so `s1ds` refuses to run the server as root.

## Quick start: Ubuntu Server (headless, over SSH)

Step 1. As your usual admin account (the one with `sudo`), install the system
packages and create a dedicated user for the server:

```bash
git clone https://github.com/bobbykdhan/LoginScript.git
sudo LoginScript/schedule1-server/s1ds deps --winehq    # Wine 11, Xvfb, SteamCMD libraries

sudo adduser --disabled-password --gecos '' schedule1   # the server runs as this user
sudo loginctl enable-linger schedule1                   # lets its service run at boot without a login

sudo ufw allow 38465/udp && sudo ufw allow 38465/tcp && sudo ufw allow 27016/udp
# (ufw is off by default on Ubuntu Server. If you turn it on, run `sudo ufw allow OpenSSH` first.)
```

If the repository is private, `git clone` asks for a GitHub username and a
personal access token. You can also copy just this folder from another
machine, e.g. `scp -r schedule1-server you@server:`.

Step 2. Switch to the server user and install the server:

```bash
sudo -iu schedule1
git clone https://github.com/bobbykdhan/LoginScript.git
cd LoginScript/schedule1-server

./s1ds install           # asks for your Steam username, password and Steam Guard code once
./s1ds run               # test run; the first start takes several minutes. Ctrl+C saves and stops
```

Step 3. When the log shows the server is up, run it in the background so it
starts at boot and keeps running after you log out of SSH:

```bash
./s1ds service install
./s1ds start
./s1ds status
./s1ds logs -f           # Ctrl+C stops following the log, not the server
```

Then forward the ports on your router (see [Ports](#ports)). Everything lives
in `/home/schedule1/schedule1-server`. To use another folder, set
`S1DS_HOME=/path` before running any command.

With only 4 GB of RAM, add swap so a memory spike does not kill the server:
`sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`.
To keep it after a reboot, add `/swapfile none swap sw 0 0` to `/etc/fstab`.

### Other distros or a desktop PC

The same steps work. Run `./s1ds deps` as a normal user with sudo rights,
then `./s1ds install` and the rest as that same user. `./s1ds firewall`
opens the ports in ufw or firewalld if one is active.

## Commands

| Command | What it does |
| --- | --- |
| `s1ds deps [--winehq]` | Installs system packages (Wine, Xvfb, cabextract, 32-bit libs). `--winehq` uses WineHQ's current Wine |
| `s1ds install` | Downloads SteamCMD, the game, the Steamworks DLLs, MelonLoader and the S1DS server mod. Also sets up the Wine prefix |
| `s1ds update [--backup]` | Updates the game and the mods. A running server is stopped, backed up and started again |
| `s1ds run` | Runs the server in the foreground. You can type console commands, and Ctrl+C saves and stops |
| `s1ds start` / `stop` / `restart` | Controls the background server. These use the systemd service if it is installed. `stop` always saves first |
| `s1ds status` | Shows install state, ports and whether the server is running and listening |
| `s1ds console` | Attaches to the live console. Ctrl+D detaches and the server keeps running |
| `s1ds cmd <command>` | Sends one command and prints the reply, e.g. `s1ds cmd listplayers` |
| `s1ds logs [-f]` | Shows or follows the server log |
| `s1ds config [server\|permissions\|s1ds]` | Edits `server_config.toml`, `permissions.toml` or `s1ds.conf` |
| `s1ds backup` | Saves the world first, then archives configs and the world to `~/schedule1-server/backups` |
| `s1ds restore <file>` | Restores a backup. Stop the server first |
| `s1ds import-save <dir>` | Copies a single-player `SaveGame_N` world into the server |
| `s1ds service install\|remove` | Adds or removes the systemd user service |

Useful console commands: `help`, `serverinfo`, `listplayers`, `save`,
`kick <player> [reason]`, `ban <player> [reason]`, `unban <steamid>`,
`op <player>`, `reloadconfig`, `reloadpermissions`, `shutdown [reason]`.

## Configuration

There are two config files:

1. **`~/schedule1-server/s1ds.conf`** holds settings for the manager script:
   runtime (`mono`/`il2cpp`), Steam username, mod versions, backup count,
   shutdown timeout and extra launch args. See [`s1ds.conf.example`](s1ds.conf.example).
2. **`~/schedule1-server/game/UserData/server_config.toml`** holds the server
   settings. `install` seeds it with the name, port, max players, password,
   Steam auth and console mode from `s1ds.conf`. On first boot the server adds
   every other option with comments. After that this file is the source of
   truth. Edit it with `s1ds config`, then run `s1ds cmd reloadconfig`. A port
   change needs `s1ds restart`.

Common settings in `server_config.toml`:

```toml
[server]
serverName = "My Schedule I Server"
maxPlayers = 8
serverPort = 38465
serverPassword = ""          # empty = no password

[gameplay]
pauseGameWhenEmpty = false   # true pauses the world when nobody is online
allowSleeping = true

[autosave]
autoSaveEnabled = true
autoSaveIntervalMinutes = 10

[performance]
targetFrameRate = 60         # 30 uses less CPU
```

### Making yourself an admin

Find your SteamID64, e.g. on steamid.io. Then run `s1ds config permissions`
and add:

```toml
[user.76561198000000000]
groups = ['operator']
```

Then run `s1ds cmd reloadpermissions`. Operators can open the in-game admin
console with the Backquote key (`` ` ``) while connected.

## Ports

| Port | Protocol | Purpose | Forward on router? |
| --- | --- | --- | --- |
| 38465 | UDP | Game traffic | Yes |
| 38465 | TCP | S1DS status query (server list / favorites) | Yes |
| 27016 | UDP | Steam query | Yes |
| 4050 | TCP | TCP admin console (off by default) | No |
| 4051 | TCP | Web panel (loopback only) | No |

If port forwarding does not work, your ISP may use CGNAT. You would then need a
public IPv4 address, IPv6, a VPN such as Tailscale or ZeroTier, or a VPS.

## How players join

Players need the matching **client** mod:

1. Use the same game branch as the server.
   - `RUNTIME="mono"` (default): in Steam, right-click Schedule I →
     **Properties → Betas** → select **alternate**.
   - `RUNTIME="il2cpp"`: stay on the normal (default) branch.
2. Install [MelonLoader](https://github.com/LavaGang/MelonLoader/releases)
   (v0.7.2 or newer, **not** 0.7.1) into the game.
3. From the [S1DS release](https://github.com/ifBars/S1DedicatedServers/releases)
   that matches the server, extract `Mono-Client.zip` (or `Il2cpp_Client.zip`)
   into the game folder.
4. Start the game, click **Servers** on the main menu, and connect to
   `your-public-ip:38465`. LAN players use the server's LAN IP.

Proton players can install MelonLoader the same way. They also need the launch
option `WINEDLLOVERRIDES="version=n,b" %command%`.

## Importing your single-player world

1. Start the server once so it creates its own world, then stop it.
2. Find your save. On Linux through Proton it is usually:
   `~/.local/share/Steam/steamapps/compatdata/3164500/pfx/drive_c/users/steamuser/AppData/LocalLow/TVGS/Schedule I/Saves/<SteamID>/SaveGame_1`
   On Windows it is `%USERPROFILE%\AppData\LocalLow\TVGS\Schedule I\Saves\<SteamID>\SaveGame_1`.
3. Run `./s1ds import-save "/path/to/SaveGame_1"`. It backs up first and keeps
   the server's internal host player (`Players/Player_0`).

## Updating

```bash
./s1ds update --backup
```

This updates the game through SteamCMD, re-applies MelonLoader and the mod,
and restarts the server if it was running. If `S1DS_VERSION="latest"`, it also
pulls the newest S1DS release. Pin a version, for example `S1DS_VERSION="v1.1.6"`,
to upgrade only when you choose. Players must update their client mod to match.

SteamCMD caches your login. If the cache expires, `update` asks for your
password or Steam Guard code again, so run it from a terminal.

## Scheduled backups (optional)

```bash
crontab -e
# every 6 hours:
0 */6 * * * S1DS_HOME=$HOME/schedule1-server /path/to/schedule1-server/s1ds backup >/dev/null 2>&1
```

## Docker alternative

If your distro's Wine gives you trouble, use the mod's official image, which
ships Wine 11. Note that the upstream image has no attachable console, so run
admin commands from the in-game console as an operator.

```bash
cd docker
cp .env.example .env     # fill in STEAM_USER / STEAM_PASS / STEAM_GUARD
docker compose up -d
docker compose logs -f
```

## Troubleshooting

- **`Do not run the server as root`.** Create the `schedule1` user as shown
  in the quick start and run everything except `deps` as that user.
- **`Wine could not create its prefix`.** Look in
  `~/schedule1-server/logs/wine-setup.log`. Check that `wine --version` works
  for the server user. Then run `sudo s1ds deps --winehq` and `s1ds install`
  again.
- **`Cannot reach your systemd user manager`.** Run
  `sudo loginctl enable-linger schedule1` from your admin account, then try
  again from `sudo -iu schedule1`.
- **The first start sits for minutes.** This is normal. MelonLoader sets up on
  first launch. IL2CPP also generates assemblies. Watch `s1ds logs -f`.
- **`Could not find Steam runtime DLLs`.** Run `s1ds update`. The Steamworks
  redistributable download (app 1007) probably failed.
- **SteamCMD fails to log in.** Check the username, that the account owns
  Schedule I, and the Steam Guard code. Run `s1ds install` again from a terminal.
- **The server starts, but nobody outside your network can join.** Forward
  38465 **UDP and TCP** plus 27016 UDP. Run `s1ds firewall`. Check for CGNAT.
- **Players get a version mismatch or are rejected.** The server and clients
  need the same game branch, the same S1DS version and the same runtime.
- **The mod broke after a Schedule I patch.** Wait for a new S1DS release, then
  run `s1ds update`.
- **Detailed logs:** `~/schedule1-server/logs/console.log`, the previous run in
  `console.log.1`, and `~/schedule1-server/game/MelonLoader/Latest.log`.
- **More help:** [S1DS docs](https://docs.s1servers.com/) and
  [issues](https://github.com/ifBars/S1DedicatedServers/issues).

## Folder layout

```
~/schedule1-server/
├── s1ds.conf            manager settings
├── game/                Schedule I (Windows build) + MelonLoader + Mods/
│   └── UserData/        server_config.toml, permissions.toml, DedicatedServerSave/ (the world)
├── wineprefix/          Wine prefix (VC++ runtime, .NET 6 for IL2CPP)
├── steamcmd/            SteamCMD
├── steamworks_redist/   Steamworks DLLs for Steam server auth
├── logs/                console.log, runner.log
├── backups/             userdata-*.tar.gz
└── run/                 console pipe, pid files, lock
```

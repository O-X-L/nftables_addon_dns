# NFTables Addon - DNS Resolution

NFTables lacks some functionality, that is commonly used in firewalling.

Having variables that hold the IPs of some DNS-record is one of those.

NFTables CAN resolve DNS-records - but will throw an error if the record resolves to more than one IP.. (`Error: Hostname resolves to multiple addresses`)

----

## Other Addons

* [IPLists](https://github.com/superstes/nftables_addon_iplist)
* [Failover](https://github.com/superstes/nftables_addon_failover)

NFTables documentation: [wiki.superstes.eu](https://wiki.superstes.eu/en/latest/1/network/firewall_nftables.html)

----

## Result

```text
cat /etc/nftables.d/addons/dns.nft
> # Auto-Generated config - DO NOT EDIT MANUALLY!
> 
> define site_github_v4 = { 140.82.121.3, 140.82.121.10 }
> define site_github_v6 = { :: }
> define repo_debian_v4 = { 151.101.86.132 }
> define repo_debian_v6 = { 2a04:4e42:14::644 }
> define ntp_pool_v4 = { 158.43.128.33, 178.62.250.107, 194.58.207.20, 37.252.127.156 }
> define ntp_pool_v6 = { :: }
```

----

## How does it work?

1. A configuration file needs to be created:

    `/etc/nftables.d/addons/dns.json`

    ```json
    {
      "dns": {
        "site_github": ["github.com", "codeload.github.com"],
        "repo_debian": "deb.debian.org",
        "ntp_pool": "europe.pool.ntp.org"
      }
    }
    ```


2. The script is executed

    `python3 /usr/lib/nftables/dns.py`

  * It will load the configuration
  * Resolve IPv4 and IPv6 (_if enabled_) for all configured variables
  * If it was unable to resolve some record - a placeholder-value will be set:

    IPv4: `0.0.0.0`

    IPv6: `::`

  * The new addon-config is written to `/tmp/nftables_dns.nft`
  * Its md5-hash is compared to the existing config to check if it changed

  * **If it has changed**:
    * **Config validation** is done:

      * An include-file is written to `/tmp/nftables_main.nft`:

        ```nft
        include /tmp/nftables_dns.nft
        # including all other adoon configs
        include /etc/nftables.d/addons/other_addon1.nft
        include /etc/nftables.d/addons/other_addon2.nft
        # include other main configs
        include /etc/nftables.d/*.nft
        ```

      * This include-file is validated:

        `sudo nft -cf /tmp/nftables_main.nft`

    * The new config is written to `/etc/nftables.d/addons/dns.nft`
    * The actual config is validated: `sudo nft -cf /etc/nftables.conf`
    * NFTables is reloaded: `sudo systemctl reload nftables.service`


3. You will have to include the addon-config in your main-config file `/etc/nftables.conf`:

    ```
    ...
    include /etc/nftables.d/addons/*.nft
    ...
    ```

----

## Privileges

If the script should be run as non-root user - you will need to add a sudoers.d file to add the needed privileges:

```text
Cmnd_Alias NFTABLES_ADDON = \
  /usr/bin/systemctl reload nftables.service,
  /usr/sbin/nft -cf *

service_user ALL=(ALL) NOPASSWD: NFTABLES_ADDON
```

You may not change the owner of the addon-files as the script will not be able to overwrite them.

----

## Safety

As explained above - there is a config-validation process to ensure the addon will not supply a bad config and lead to a failed nftables reload/restart.

If you want to be even safer - you can add a config-validation inside the `nftables.service`:

```text
# /etc/systemd/system/nftables.service.d/override.conf
[Service]
# catch errors at start
ExecStartPre=/usr/sbin/nft -cf /etc/nftables.conf

# catch errors at reload
ExecReload=
ExecReload=/usr/sbin/nft -cf /etc/nftables.conf
ExecReload=/usr/sbin/nft -f /etc/nftables.conf

# catch errors at restart
ExecStop=
ExecStop=/usr/sbin/nft -cf /etc/nftables.conf
ExecStop=/usr/sbin/nft flush ruleset

Restart=on-failure
RestartSec=5s
```

This will catch and log config-errors before doing a reload/restart.

----

## Scheduling

You can either:

* Add a Systemd Timer: [example](https://github.com/ansibleguy/addons_nftables/tree/latest/templates/etc/systemd/system)
* Add a cron job

----

## Ansible

Here you can find an Ansible Role to manage NFTables Addons:

* [ansibleguy.addons_nftables](https://github.com/ansibleguy/addons_nftables)
* [examples](https://github.com/ansibleguy/addons_nftables/blob/latest/Example.md)

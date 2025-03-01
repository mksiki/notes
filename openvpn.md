# To-go command for openvpns

I came across an error when trying to connect to HTB labs. Simple error, nothing that would break it. 

`WARNING: Compression for receiving enabled. Compression has been used in the past to break encryption. Sent packets are not compressed unless "allow-compression yes" is also set.
2024-07-06 01:33:23 Note: --data-cipher-fallback with cipher 'AES-128-CBC' disables data channel offload.
 `

 `2024-07-06 02:14:07 ERROR: Cannot ioctl TUNSETIFF tun: Operation not permitted (errno=1)
2024-07-06 02:14:07 Exiting due to fatal error`

If you having this same issue and as a reminder for me, try this

`sudo openvpn --config <filename> --daemon &>/dev/null`

I have never had any issues connecting to any vpn with this. 

package cmd

import (
	"bufio"
	"encoding/base64"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/AlecAivazis/survey/v2"
	"github.com/rs/zerolog/log"

	"github.com/davegallant/vpngate/pkg/vpn"
	"github.com/go-toast/toast"
	"github.com/spf13/cobra"
)

var (
	flagRandom      bool
	flagReconnect   bool
	flagProxy       string
	flagSocks5Proxy string
	statusFile      = "log\\log.txt"
	isVpnAlive      = false
)

func init() {
	connectCmd.Flags().BoolVarP(&flagRandom, "random", "r", false, "connect to a random server")
	connectCmd.Flags().BoolVarP(&flagReconnect, "reconnect", "t", false, "continually attempt to connect to the server")
	connectCmd.Flags().StringVarP(&flagProxy, "proxy", "p", "", "provide a http/https proxy server to make requests through (i.e. http://127.0.0.1:8080)")
	connectCmd.Flags().StringVarP(&flagSocks5Proxy, "socks5", "s", "", "provide a socks5 proxy server to make requests through (i.e. 127.0.0.1:1080)")
	rootCmd.AddCommand(connectCmd)
}

var connectCmd = &cobra.Command{
	Use: "connect",

	Short: "Connect to a vpn server (survey selection appears if hostname is not provided)",
	Long:  `Connect to a vpn from a list of relay servers`,
	Args:  cobra.RangeArgs(0, 1),
	Run: func(cmd *cobra.Command, args []string) {
		vpnServers, err := vpn.GetList(flagProxy, flagSocks5Proxy)
		if err != nil {
			log.Fatal().Msgf(err.Error())
			os.Exit(1)
		}

		serverSelection := []string{}
		serverSelected := vpn.Server{}

		for i, s := range *vpnServers {
			serverSelection = append(serverSelection, fmt.Sprintf("%2d/%-2d %-16s (%-7s-%-2s)", i+1, len(*vpnServers), s.HostName, s.CountryLong, s.CountryShort))
		}

		selection := ""
		prompt := &survey.Select{
			Message: "Choose a server:",
			Options: serverSelection,
		}

		if !flagRandom {

			if len(args) > 0 {
				selection = args[0]
			} else {
				err := survey.AskOne(prompt, &selection, survey.WithPageSize(10))
				if err != nil {
					log.Error().Msg("Unable to obtain hostname from survey")
					os.Exit(1)
				}
			}

			// Server lookup from selection could be more optimized with a hash map
			for _, s := range *vpnServers {
				if strings.Contains(selection, s.HostName) {
					serverSelected = s
				}
			}

			if serverSelected.HostName == "" {
				log.Fatal().Msgf("Server '%s' was not found", selection)
				os.Exit(1)
			}
		}
		serverSelectedIndex := 0
		for i, s := range *vpnServers {
			if strings.Contains(selection, s.HostName) {
				serverSelectedIndex = i
			}
		}
		for i := serverSelectedIndex; i < len(*vpnServers); i++ {
			serverSelected = (*vpnServers)[i]
			if flagRandom {
				// Select a random server
				rand.Seed(time.Now().UnixNano())
				serverSelected = (*vpnServers)[rand.Intn(len(*vpnServers))]
			}

			decodedConfig, err := base64.StdEncoding.DecodeString(serverSelected.OpenVpnConfigData)
			if err != nil {
				log.Fatal().Msgf("解析错误：%s", err.Error())
				os.Exit(1)
			}

			tmpfile, err := os.CreateTemp("", "vpngate-openvpn-config-")
			if err != nil {
				log.Fatal().Msgf("临时文件创建错误：%s", err.Error())
				os.Exit(1)
			}

			if _, err := tmpfile.Write(decodedConfig); err != nil {
				log.Fatal().Msgf("解析配置错误：%s", err.Error())
				os.Exit(1)
			}

			if err := tmpfile.Close(); err != nil {
				log.Fatal().Msgf("关闭错误：%s", err.Error())
				os.Exit(1)
			}

			log.Info().Msgf("正在尝试连接到服务器 %-16s 国家 %s [ %d/%d ]", serverSelected.HostName, serverSelected.CountryShort, i+1, len(*vpnServers))

			err = vpn.Connect(tmpfile.Name(), statusFile)

			if err != nil {
				log.Error().Msg("连接失败！")
				os.Remove(tmpfile.Name())
				if flagReconnect {
					break
				}
				log.Info().Msg("...")
				continue
			} else {
				os.Remove(tmpfile.Name())

				log.Info().Msgf("成功连接到%s(%s) %s (%d/%d)", serverSelected.HostName, serverSelected.IPAddr, serverSelected.CountryLong, i+1, len(*vpnServers))
				// 启动状态监控
				go monitorOpenVPNStatus(statusFile)
				if !isVpnAlive {
					time.Sleep(5 * time.Second)
					if !isVpnAlive {
						vpn.Disconnect()
						if err != nil {
							log.Fatal().Msg("断开失败")
							os.Exit(1)
						}
						continue
					}

				}

				// 添加一个循环来保持程序运行并允许用户交互
				fmt.Println("输入 'q' 或 'quit' 来断开连接并退出")
				scanner := bufio.NewScanner(os.Stdin)

				for {
					fmt.Print("> ")
					scanner.Scan()
					command := scanner.Text()

					switch strings.ToLower(command) {
					case "q", "quit":
						log.Debug().Msg("正在断开连接...")
						err := vpn.Disconnect()
						if err != nil {
							log.Fatal().Msg("断开失败")
							os.Exit(1)
						}
						os.Remove(statusFile)
						log.Info().Msg("已断开vpn连接！")
						return
					case "status":
						// 显示vpn连接状态
						currentStatus, err := getCurrentStatus(statusFile)
						if err != nil {
							log.Error().Err(err).Msg("无法获取VPN状态")
						} else {
							if isVpnAlive {
								log.Info().Msgf("vpn连接正常 %s", currentStatus)
							} else {
								os.Remove(statusFile)
								log.Warn().Msgf("vpn连接断开 %s", currentStatus)
							}

						}
					default:
						log.Info().Msg("未知命令. 可用命令: quit, status")
					}
				}
			}
		}
	},
}

// monitorOpenVPNStatus 定期检查 OpenVPN 的状态
func monitorOpenVPNStatus(statusFile string) {
	lastTunReadBytes := 0
	lastTunWriteBytes := 0
	lastCheckedTime := time.Now()

	time.Sleep(2 * time.Second)
	currentTunReadBytes, currentTunWriteBytes, err := getTunBytes(statusFile)
	if err != nil {
		log.Error().Err(err).Msg("无法读取 OpenVPN 状态文件")
	}
	if currentTunReadBytes > 0 && currentTunWriteBytes > 0 {
		showNotification(time.Now().Format("vpn服务器"), "连接成功")
	}

	for {
		currentTunReadBytes, currentTunWriteBytes, err := getTunBytes(statusFile)
		if err != nil {
			log.Error().Err(err).Msg("无法读取 OpenVPN 状态文件")
			time.Sleep(10 * time.Second)
			continue
		}

		// 检查读写字节数是否变化
		if currentTunReadBytes != lastTunReadBytes || currentTunWriteBytes != lastTunWriteBytes {
			// showNotification("OpenVPN", "连接正常")
			isVpnAlive = true
			lastTunReadBytes = currentTunReadBytes
			lastTunWriteBytes = currentTunWriteBytes
			lastCheckedTime = time.Now()
		} else {
			duration := time.Since(lastCheckedTime)
			if duration.Seconds() > 20 { // 如果20秒内没有变化，认为连接断开
				isVpnAlive = false
				showNotification("vpn服务器", "连接断开")
			}
		}

		time.Sleep(2 * time.Second)
	}
}

// getTunBytes 读取状态文件并返回 TUN/TAP 读写字节数
func getTunBytes(statusFile string) (int, int, error) {
	file, err := os.Open(statusFile)
	if err != nil {
		return 0, 0, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	tunReadBytes := 0
	tunWriteBytes := 0
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) == 2 {
			if fields[0] == "TUN/TAP read bytes" {
				tunReadBytes, err = strconv.Atoi(fields[1])
				if err != nil {
					return 0, 0, err
				}
			}
			if fields[0] == "TUN/TAP write bytes" {
				tunWriteBytes, err = strconv.Atoi(fields[1])
				if err != nil {
					return 0, 0, err
				}
			}
		}
	}

	return tunReadBytes, tunWriteBytes, nil
}

func getExecutablePath() (string, error) {
	exePath, err := os.Executable()
	if err != nil {
		return "", err
	}
	return filepath.Dir(exePath), nil
}

// showNotification 显示Windows通知
func showNotification(title, message string) {
	if runtime.GOOS == "windows" {
		exePath, err := getExecutablePath()
		if err != nil {
			log.Error().Err(err).Msg("无法获取可执行文件路径")
			return
		}
		iconPath := filepath.Join(exePath, "logo.png") // 拼接相对路径

		notification := toast.Notification{
			AppID:   "OpenVPN",
			Title:   title,
			Message: message,
			Icon:    iconPath, // 可选: 设置图标路径
		}
		err2 := notification.Push()
		if err2 != nil {
			log.Error().Err(err).Msg("无法发送通知")
		}
	}
}

// getCurrentStatus 获取当前VPN连接状态
func getCurrentStatus(statusFile string) (string, error) {
	tunReadBytes, tunWriteBytes, err := getTunBytes(statusFile)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("read: %d, write: %d", tunReadBytes, tunWriteBytes), nil
}

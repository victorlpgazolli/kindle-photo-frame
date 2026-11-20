package main

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"os"
	"time"
)

func main() {
	mode, listenAddr, targetAddr := os.Args[1], os.Args[2], os.Args[3]
	if mode == "tcp2udp" {
		ln, err := net.Listen("tcp", listenAddr)
		if err != nil { panic(err) }
		fmt.Println("Listening TCP on", listenAddr, "-> UDP", targetAddr)
		for {
			c, err := ln.Accept()
			if err != nil { continue }
			go func(conn net.Conn) {
				defer conn.Close()
				u, err := net.Dial("udp", targetAddr)
				if err != nil { return }
				defer u.Close()
				go func() {
					buf := make([]byte, 2048)
					for {
						n, err := u.Read(buf)
						if err != nil { return }
						var lenBuf [2]byte
						binary.BigEndian.PutUint16(lenBuf[:], uint16(n))
						if _, err := conn.Write(lenBuf[:]); err != nil { return }
						if _, err := conn.Write(buf[:n]); err != nil { return }
					}
				}()
				var lenBuf [2]byte
				for {
					if _, err := io.ReadFull(conn, lenBuf[:]); err != nil { return }
					l := binary.BigEndian.Uint16(lenBuf[:])
					pkt := make([]byte, l)
					if _, err := io.ReadFull(conn, pkt); err != nil { return }
					u.Write(pkt)
				}
			}(c)
		}
	} else {
		uAddr, err := net.ResolveUDPAddr("udp", listenAddr)
		if err != nil { panic(err) }
		uConn, err := net.ListenUDP("udp", uAddr)
		if err != nil { panic(err) }
		fmt.Println("Listening UDP on", listenAddr, "-> TCP", targetAddr)

		var tConn net.Conn
		var clientAddr *net.UDPAddr
		buf := make([]byte, 2048)

		for {
			n, addr, err := uConn.ReadFromUDP(buf)
			if err != nil { continue }
			clientAddr = addr

			if tConn == nil {
				c, err := net.DialTimeout("tcp", targetAddr, 5*time.Second)
				if err != nil {
					fmt.Println("Dial TCP err:", err)
					continue
				}
				tConn = c
				fmt.Println("Connected TCP tunnel -> forwarding handshake")
				go func(conn net.Conn) {
					var lenBuf [2]byte
					for {
						if _, err := io.ReadFull(conn, lenBuf[:]); err != nil {
							tConn = nil
							return
						}
						l := binary.BigEndian.Uint16(lenBuf[:])
						pkt := make([]byte, l)
						if _, err := io.ReadFull(conn, pkt); err != nil {
							tConn = nil
							return
						}
						if clientAddr != nil {
							uConn.WriteToUDP(pkt, clientAddr)
						}
					}
				}(tConn)
			}

			var lenBuf [2]byte
			binary.BigEndian.PutUint16(lenBuf[:], uint16(n))
			if _, err := tConn.Write(lenBuf[:]); err != nil {
				tConn.Close()
				tConn = nil
			} else if _, err := tConn.Write(buf[:n]); err != nil {
				tConn.Close()
				tConn = nil
			}
		}
	}
}

import { useState, useEffect, useRef, useCallback } from "react";
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  Animated,
  ActivityIndicator,
  Dimensions,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImageManipulator from "expo-image-manipulator";

const { width } = Dimensions.get("window");
const WS_URL = "ws://10.188.189.151:8000/ws/ocr";
const CAPTURE_INTERVAL_MS = 800;

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const cameraRef = useRef(null);
  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const resultSlide = useRef(new Animated.Value(60)).current;

  useEffect(() => {
    if (scanning) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.08,
            duration: 700,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 700,
            useNativeDriver: true,
          }),
        ]),
      ).start();
    } else {
      pulseAnim.stopAnimation();
      pulseAnim.setValue(1);
    }
  }, [scanning]);

  useEffect(() => {
    if (result) {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 260,
          useNativeDriver: true,
        }),
        Animated.timing(resultSlide, {
          toValue: 0,
          duration: 260,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      fadeAnim.setValue(0);
      resultSlide.setValue(60);
    }
  }, [result]);

  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setWsStatus("connecting");
    setError(null);
    console.log("creating websocket...");
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      setWsStatus("connected");
      setError(null);
    };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.building !== undefined) {
          setResult({
            building: data.building,
            confidence: data.confidence ?? null,
          });
        } else if (data.error) {
          setError(data.error);
        } else if (data.text) {
          setResult({ building: data.text, confidence: null });
        }
      } catch {
        setResult({ building: e.data, confidence: null });
      }
    };
    ws.onerror = () => {
      setWsStatus("error");
      setError("WebSocket error. Is the server running on :8000?");
    };
    ws.onclose = () => {
      setWsStatus("disconnected");
      stopScanning();
    };
    wsRef.current = ws;
  }, []);

  const disconnectWS = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const captureAndSend = useCallback(async () => {
    if (!cameraRef.current || wsRef.current?.readyState !== WebSocket.OPEN)
      return;
    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.5,
        skipProcessing: true,
      });
      const resized = await ImageManipulator.manipulateAsync(
        photo.uri,
        [{ resize: { width: 640 } }],
        {
          compress: 0.6,
          format: ImageManipulator.SaveFormat.JPEG,
          base64: true,
        },
      );
      if (resized.base64) {
        wsRef.current.send(JSON.stringify({ image: resized.base64 }));
      }
    } catch (err) {
      console.warn("Capture error:", err);
    }
  }, []);

  const startScanning = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    setScanning(true);
    setResult(null);
    intervalRef.current = setInterval(captureAndSend, CAPTURE_INTERVAL_MS);
  }, [captureAndSend]);

  const stopScanning = useCallback(() => {
    setScanning(false);
    clearInterval(intervalRef.current);
    intervalRef.current = null;
  }, []);

  useEffect(
    () => () => {
      clearInterval(intervalRef.current);
      wsRef.current?.close();
    },
    [],
  );

  if (!permission) return <View style={styles.container} />;
  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={styles.centered}>
          <Text style={styles.permTitle}>Camera Access Needed</Text>
          <Text style={styles.permSub}>
            Label Reader needs your camera to scan mailroom labels.
          </Text>
          <TouchableOpacity
            style={styles.primaryBtn}
            onPress={requestPermission}>
            <Text style={styles.primaryBtnText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const isConnected = wsStatus === "connected";
  const confidencePercent =
    result?.confidence != null
      ? `${Math.round(result.confidence * 100)}%`
      : null;
  const confidenceColor =
    result?.confidence == null
      ? "#8E9AAF"
      : result.confidence > 0.8
        ? "#4ADE80"
        : result.confidence > 0.5
          ? "#FACC15"
          : "#F87171";

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        facing="back"
      />
      <View style={styles.vignette} pointerEvents="none" />

      <SafeAreaView style={styles.safeHeader}>
        <View style={styles.header}>
          <Text style={styles.appTitle}>
            LABEL<Text style={styles.titleAccent}> READER</Text>
          </Text>
          <View style={[styles.statusDot, styles[`status_${wsStatus}`]]} />
        </View>
      </SafeAreaView>

      <View style={styles.scanFrame} pointerEvents="none">
        <Animated.View
          style={[styles.scanRing, { transform: [{ scale: pulseAnim }] }]}>
          <View style={styles.cornerTL} />
          <View style={styles.cornerTR} />
          <View style={styles.cornerBL} />
          <View style={styles.cornerBR} />
        </Animated.View>
        {scanning && <Text style={styles.scanHint}>Hover over a label</Text>}
      </View>

      {result && (
        <Animated.View
          style={[
            styles.resultCard,
            { opacity: fadeAnim, transform: [{ translateY: resultSlide }] },
          ]}>
          <Text style={styles.resultBuilding}>{result.building}</Text>
          {confidencePercent && (
            <View style={styles.confidenceRow}>
              <Text style={styles.confidenceLabel}>Confidence</Text>
              <Text
                style={[styles.confidenceValue, { color: confidenceColor }]}>
                {confidencePercent}
              </Text>
            </View>
          )}
        </Animated.View>
      )}

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <SafeAreaView style={styles.safeBottom}>
        <View style={styles.controls}>
          <TouchableOpacity
            style={[
              styles.secondaryBtn,
              isConnected && styles.secondaryBtnActive,
            ]}
            onPress={isConnected ? disconnectWS : connectWS}
            disabled={wsStatus === "connecting"}>
            {wsStatus === "connecting" ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.secondaryBtnText}>
                {isConnected ? "Disconnect" : "Connect"}
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.scanBtn,
              scanning && styles.scanBtnActive,
              !isConnected && styles.scanBtnDisabled,
            ]}
            onPress={scanning ? stopScanning : startScanning}
            disabled={!isConnected}
            activeOpacity={0.8}>
            <View
              style={[
                styles.scanBtnInner,
                scanning && styles.scanBtnInnerActive,
              ]}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.secondaryBtn, !result && { opacity: 0.3 }]}
            onPress={() => setResult(null)}
            disabled={!result}>
            <Text style={styles.secondaryBtnText}>Clear</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.wsUrl}>{WS_URL}</Text>
      </SafeAreaView>
    </View>
  );
}

const CORNER = 22;
const FRAME_SIZE = width * 0.72;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0A0A0F" },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
  },
  permTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#F0F0F5",
    marginBottom: 10,
  },
  permSub: {
    fontSize: 15,
    color: "#8E9AAF",
    textAlign: "center",
    marginBottom: 32,
    lineHeight: 22,
  },
  vignette: { ...StyleSheet.absoluteFillObject },
  safeHeader: { position: "absolute", top: 0, left: 0, right: 0 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 12,
    backgroundColor: "rgba(10,10,15,0.75)",
  },
  appTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: "#F0F0F5",
    letterSpacing: 3,
  },
  titleAccent: { color: "#3B82F6" },
  statusDot: { width: 10, height: 10, borderRadius: 5 },
  status_disconnected: { backgroundColor: "#4B5563" },
  status_connecting: { backgroundColor: "#FACC15" },
  status_connected: { backgroundColor: "#4ADE80" },
  status_error: { backgroundColor: "#F87171" },
  scanFrame: {
    position: "absolute",
    top: "50%",
    left: "50%",
    width: FRAME_SIZE,
    height: FRAME_SIZE * 0.55,
    marginLeft: -FRAME_SIZE / 2,
    marginTop: -(FRAME_SIZE * 0.55) / 2 - 40,
    alignItems: "center",
    justifyContent: "flex-end",
  },
  scanRing: { ...StyleSheet.absoluteFillObject },
  cornerTL: {
    position: "absolute",
    top: 0,
    left: 0,
    width: CORNER,
    height: CORNER,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderColor: "#3B82F6",
    borderRadius: 2,
  },
  cornerTR: {
    position: "absolute",
    top: 0,
    right: 0,
    width: CORNER,
    height: CORNER,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderColor: "#3B82F6",
    borderRadius: 2,
  },
  cornerBL: {
    position: "absolute",
    bottom: 0,
    left: 0,
    width: CORNER,
    height: CORNER,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderColor: "#3B82F6",
    borderRadius: 2,
  },
  cornerBR: {
    position: "absolute",
    bottom: 0,
    right: 0,
    width: CORNER,
    height: CORNER,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderColor: "#3B82F6",
    borderRadius: 2,
  },
  scanHint: {
    marginBottom: -28,
    color: "rgba(240,240,245,0.6)",
    fontSize: 12,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    fontWeight: "600",
  },
  resultCard: {
    position: "absolute",
    bottom: 170,
    left: 24,
    right: 24,
    backgroundColor: "rgba(15,15,22,0.92)",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "rgba(59,130,246,0.35)",
    padding: 20,
  },
  resultBuilding: {
    fontSize: 26,
    fontWeight: "700",
    color: "#F0F0F5",
    letterSpacing: 0.4,
    marginBottom: 8,
  },
  confidenceRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  confidenceLabel: {
    fontSize: 12,
    color: "#8E9AAF",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  confidenceValue: { fontSize: 14, fontWeight: "700" },
  errorBanner: {
    position: "absolute",
    bottom: 170,
    left: 24,
    right: 24,
    backgroundColor: "rgba(248,63,63,0.15)",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(248,63,63,0.4)",
    padding: 14,
  },
  errorText: { color: "#FCA5A5", fontSize: 13, textAlign: "center" },
  safeBottom: { position: "absolute", bottom: 0, left: 0, right: 0 },
  controls: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 40,
    paddingTop: 16,
    paddingBottom: 8,
    backgroundColor: "rgba(10,10,15,0.85)",
  },
  wsUrl: {
    textAlign: "center",
    color: "rgba(142,154,175,0.5)",
    fontSize: 10,
    letterSpacing: 0.5,
    paddingBottom: 6,
    backgroundColor: "rgba(10,10,15,0.85)",
  },
  scanBtn: {
    width: 70,
    height: 70,
    borderRadius: 35,
    borderWidth: 3,
    borderColor: "#3B82F6",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(59,130,246,0.12)",
  },
  scanBtnActive: {
    borderColor: "#F87171",
    backgroundColor: "rgba(248,113,113,0.12)",
  },
  scanBtnDisabled: {
    borderColor: "#374151",
    backgroundColor: "transparent",
    opacity: 0.4,
  },
  scanBtnInner: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#3B82F6",
  },
  scanBtnInnerActive: {
    backgroundColor: "#F87171",
    borderRadius: 8,
    width: 22,
    height: 22,
  },
  primaryBtn: {
    backgroundColor: "#3B82F6",
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 32,
  },
  primaryBtnText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  secondaryBtn: {
    borderWidth: 1,
    borderColor: "#374151",
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 18,
    backgroundColor: "rgba(255,255,255,0.04)",
  },
  secondaryBtnActive: {
    borderColor: "#4ADE80",
    backgroundColor: "rgba(74,222,128,0.08)",
  },
  secondaryBtnText: { color: "#D1D5DB", fontWeight: "600", fontSize: 14 },
});

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
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  useWindowDimensions,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImageManipulator from "expo-image-manipulator";

// ─── Responsive helpers ──────────────────────────────────────────────────────
// A hook that returns live screen metrics + derived design tokens so every
// component re-renders correctly on orientation changes and on tablets.

function useResponsive() {
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;
  const isTablet = Math.min(width, height) >= 600;
  const isSmall = Math.min(width, height) < 375; // SE / older Androids

  // Base unit — everything scales off this
  const base = isTablet ? 9 : isSmall ? 6 : 7.5;

  return {
    width,
    height,
    isLandscape,
    isTablet,
    isSmall,
    // Spacing scale
    sp: (n) => Math.round(base * n),
    // Font scale
    fs: (n) => Math.round((isTablet ? 1.22 : isSmall ? 0.88 : 1) * n),
    // Scan frame: 72% wide in portrait, 45% wide in landscape (otherwise off-screen)
    frameW: isLandscape ? width * 0.45 : width * 0.72,
    // Button / icon sizes
    scanBtnSize: isTablet ? 96 : isSmall ? 68 : 80,
    cornerSize: isTablet ? 28 : isSmall ? 18 : 22,
  };
}

// ─── Constants ───────────────────────────────────────────────────────────────
const WS_URL = "wss://label-reader.railway.app/ws/ocr";

// ─── Main Component ──────────────────────────────────────────────────────────
export default function App({ navigation }) {
  const R = useResponsive();
  const { width, height, isLandscape, isTablet, sp, fs, frameW, scanBtnSize, cornerSize } = R;

  const [permission, requestPermission] = useCameraPermissions();
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);
  const [visible, setVisible] = useState(false);
  const [visibleManual, setVisibleManual] = useState(false);
    const [form, setForm] = useState({ name: null, department: null, building: null, room: null, school: null });
    const [search, setSearch] = useState(null);

  const cameraRef = useRef(null);
  const wsRef = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const resultSlide = useRef(new Animated.Value(60)).current;

  // ── Pulse while scanning
  useEffect(() => {
    if (scanning) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.08, duration: 700, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 700, useNativeDriver: true }),
        ])
      ).start();
    } else {
      pulseAnim.stopAnimation();
      pulseAnim.setValue(1);
    }
  }, [scanning]);

  // ── Slide-in result card
  useEffect(() => {
    if (result) {
      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 280, useNativeDriver: true }),
        Animated.timing(resultSlide, { toValue: 0, duration: 280, useNativeDriver: true }),
      ]).start();
    } else {
      fadeAnim.setValue(0);
      resultSlide.setValue(60);
    }
  }, [result]);

  // ── WebSocket
  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setWsStatus("connecting");
    setError(null);
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => { setWsStatus("connected"); setError(null); console.log("WebSocket connected"); };
    ws.onmessage = (e) => {
      try {
          const data = JSON.parse(e.data);
          console.log(data)
        if (data.department !== undefined) {
          setResult({ department: data.department, confidence: data.confidence ?? null, name: data.name ?? null });
          setForm({ name: data.name ?? null, department: data.department, building: data.building ?? null, room: data.room ?? null, school: data.school ?? null });
        } else if (data.error) {
          setError(data.error);
        } else if (data.text) {
          setResult({ department: data.text, confidence: null, name: data.name ?? null });
        } else if (data.status) {
          setStatusMsg(data.status);
        } else if (data === null) {
            setError('Person Not Found')
        }
      } catch {
        setResult({ department: e?.data ?? 'Person not found', confidence: null });
      }
    };
    ws.onerror = () => { setWsStatus("error"); setError("Connection error. Please try again."); };
    ws.onclose = () => setWsStatus("disconnected");
    wsRef.current = ws;
  }, []);

  const disconnectWS = useCallback(() => { wsRef.current?.close(); wsRef.current = null; }, []);

  const addPerson = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ addPerson: true, ...form }));
    setForm({ name: "", department: "", building: "", room: "", school: "" });
  }, [form]);
    
    const searchPerson = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ searchPerson: true, 'search': search }));
  }, [search]);

  const captureOnce = useCallback(async () => {
    if (!cameraRef.current || wsRef.current?.readyState !== WebSocket.OPEN) return;
    setScanning(true);
    setResult(null);
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.5, skipProcessing: true });
      const photoWidth = photo.height;
      const photoHeight = photo.width;
      const fw = Math.min(photoWidth * 0.7, photoWidth);
      const fh = Math.min(fw * 0.25, photoHeight);
      const ox = Math.max((photoWidth - fw) / 2, 0);
      const oy = Math.max((photoHeight - fh) / 2, 0);
      const resized = await ImageManipulator.manipulateAsync(
        photo.uri,
        [{ crop: { originX: ox, originY: oy, width: Math.min(fw, photoWidth - ox), height: Math.min(fh, photoHeight - oy) } }, { resize: { width: 640 } }],
        { compress: 0.6, format: ImageManipulator.SaveFormat.JPEG, base64: true }
      );
      if (resized.base64) wsRef.current.send(JSON.stringify({ ocr: true, image: resized.base64 }));
    } catch (err) {
      console.warn("Capture error:", err);
    } finally {
      setScanning(false);
    }
  }, []);

  // ── Permission screen
  if (!permission) return <View style={{ flex: 1, backgroundColor: "#080D14" }} />;
  if (!permission.granted) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: "#080D14", alignItems: "center", justifyContent: "center", padding: sp(4) }}>
        <StatusBar barStyle="light-content" />
        <View style={{ width: sp(10), height: sp(10), borderRadius: sp(3), backgroundColor: "rgba(56,189,248,0.1)", borderWidth: 1.5, borderColor: "rgba(56,189,248,0.3)", alignItems: "center", justifyContent: "center", marginBottom: sp(4) }}>
          <View style={{ width: sp(4), height: sp(4), borderRadius: sp(2), borderWidth: 2.5, borderColor: "#38BDF8" }} />
        </View>
        <Text style={{ fontSize: fs(24), fontWeight: "800", color: "#F0F9FF", letterSpacing: -0.6, marginBottom: sp(1.5), textAlign: "center" }}>Camera Required</Text>
        <Text style={{ fontSize: fs(15), color: "#64748B", textAlign: "center", marginBottom: sp(5), lineHeight: fs(15) * 1.6, maxWidth: 300 }}>Label Reader needs camera access to scan and identify mailroom labels.</Text>
        <TouchableOpacity onPress={requestPermission} activeOpacity={0.85} style={{ backgroundColor: "#0EA5E9", borderRadius: sp(1.8), paddingVertical: sp(2), paddingHorizontal: sp(6) }}>
          <Text style={{ color: "#fff", fontWeight: "700", fontSize: fs(16), letterSpacing: 0.3 }}>Enable Camera</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  // ── Derived display values
  const isConnected = wsStatus === "connected";
  const confidencePercent = result?.confidence != null ? `${Math.round(result.confidence * 100)}%` : null;
  const confidenceColor = result?.confidence == null ? "#94A3B8" : result.confidence > 0.8 ? "#34D399" : result.confidence > 0.5 ? "#FBBF24" : "#F87171";
  const frameH = frameW * 0.26;

  // ── Layout helpers: in landscape we push result card to the side, not bottom
  const resultCardStyle = isLandscape
    ? { position: "absolute", top: sp(2), right: sp(2), width: Math.min(width * 0.36, 320), bottom: sp(14) }
    : { position: "absolute", bottom: scanBtnSize + sp(12), left: sp(2.5), right: sp(2.5) };

  const errorBannerStyle = isLandscape
    ? { position: "absolute", top: sp(2), right: sp(2), width: Math.min(width * 0.36, 320) }
    : { position: "absolute", bottom: scanBtnSize + sp(12), left: sp(2.5), right: sp(2.5) };

  return (
    <View style={{ flex: 1, backgroundColor: "#080D14" }}>
      <StatusBar barStyle="light-content" />

      {/* Camera */}
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />

      {/* Vignette overlays */}
      <View style={{ position: "absolute", top: 0, left: 0, right: 0, height: height * 0.28, backgroundColor: "rgba(8,13,20,0.82)" }} pointerEvents="none" />
      <View style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: height * 0.32, backgroundColor: "rgba(8,13,20,0.88)" }} pointerEvents="none" />

      {/* ── Header ── */}
      <SafeAreaView style={{ position: "absolute", top: 0, left: 0, right: 0, zIndex: 10 }}>
        <View style={{
          flexDirection: "row", alignItems: "center", justifyContent: "space-between",
          paddingHorizontal: sp(2.5),
          paddingTop: isLandscape ? sp(1) : sp(2),
          paddingBottom: sp(1.5),
        }}>
          {/* Logo + title */}
          <View style={{ flexDirection: "row", alignItems: "center", gap: sp(1.5), marginTop: StatusBar.currentHeight+ 5  }}>
            <View style={{
              width: isTablet ? 52 : 42, height: isTablet ? 52 : 42,
              borderRadius: isTablet ? 16 : 12,
              backgroundColor: "rgba(14,165,233,0.12)",
              borderWidth: 1, borderColor: "rgba(14,165,233,0.28)",
                          alignItems: "center", justifyContent: "center",
              
            }}>
              {/* Scan icon */}
              <View style={{ width: isTablet ? 26 : 22, height: isTablet ? 19 : 16, borderWidth: 2, borderColor: "#0EA5E9", borderRadius: 3, alignItems: "center", justifyContent: "center" }}>
                <View style={{ width: isTablet ? 14 : 11, height: 2, backgroundColor: "#0EA5E9" }} />
              </View>
            </View>
            <View>
              <Text style={{ fontSize: fs(17), fontWeight: "800", color: "#F0F9FF", letterSpacing: -0.4}}>Label Reader</Text>
              <Text style={{ fontSize: fs(11), color: "#475569", fontWeight: "500", marginTop: 1 }}>OCR Scanner</Text>
            </View>
          </View>

          {/* Status pill */}
          <View style={{
            flexDirection: "row", alignItems: "center",
            backgroundColor: "rgba(15,23,40,0.75)",
            paddingHorizontal: sp(1.5), paddingVertical: sp(0.9),
            borderRadius: 40, gap: sp(0.8),
            borderWidth: 1, borderColor: "rgba(148,163,184,0.12)",
          }}>
            <View style={{
              width: isTablet ? 10 : 8, height: isTablet ? 10 : 8, borderRadius: 5,
              backgroundColor: wsStatus === "connected" ? "#34D399" : wsStatus === "connecting" ? "#FBBF24" : wsStatus === "error" ? "#F87171" : "#475569",
            }} />
            <Text style={{ fontSize: fs(12), fontWeight: "600", color: "#94A3B8" }}>
              {wsStatus === "connected" ? "Online" : wsStatus === "connecting" ? "Connecting…" : "Offline"}
            </Text>
          </View>
        </View>
      </SafeAreaView>

      {/* ── Scan Frame (centered in camera area) ── */}
      {/* We position it in the center of the viewport minus bottom controls */}
      <View style={{
        position: "absolute",
        top: isLandscape ? "38%" : "42%",
        left: "50%",
        width: frameW,
        height: frameH,
        marginLeft: -frameW / 2,
        marginTop: -frameH / 2,
        alignItems: "center",
              justifyContent: "flex-end",
        marginTop: StatusBar.currentHeight 
      }} pointerEvents="none">
        <Animated.View style={{ ...StyleSheet.absoluteFillObject, transform: [{ scale: pulseAnim }] }}>
          {/* Corners */}
          {[
            { top: 0, left: 0, borderTopWidth: 3, borderLeftWidth: 3, borderTopLeftRadius: 8 },
            { top: 0, right: 0, borderTopWidth: 3, borderRightWidth: 3, borderTopRightRadius: 8 },
            { bottom: 0, left: 0, borderBottomWidth: 3, borderLeftWidth: 3, borderBottomLeftRadius: 8 },
            { bottom: 0, right: 0, borderBottomWidth: 3, borderRightWidth: 3, borderBottomRightRadius: 8 },
          ].map((s, i) => (
            <View key={i} style={{ position: "absolute", width: cornerSize, height: cornerSize, borderColor: "#0EA5E9", ...s }} />
          ))}
          {/* Center scan line */}
          <View style={{ position: "absolute", top: "50%", left: cornerSize, right: cornerSize, height: 1.5, backgroundColor: "rgba(14,165,233,0.45)" }} />
        </Animated.View>
        <Text style={{
          marginTop: sp(2),
          color: scanning ? "#0EA5E9" : "#64748B",
          fontSize: fs(12),
          letterSpacing: 0.6,
          fontWeight: "600",
        }}>
          {scanning ? "SCANNING…" : "ALIGN LABEL WITHIN FRAME"}
        </Text>
      </View>

      {/* ── Add Person button (top strip, only when connected) ── */}
          {isConnected && (
        <SafeAreaView style={{ position: "absolute", top: isTablet ? 80 : 70, left: 0, right: 0, zIndex: 8, alignItems: isLandscape ? "flex-start" : "center", paddingLeft: isLandscape ? sp(2.5) : 0 , marginTop: StatusBar.currentHeight+ 5 }}>
                  <View style={{
                      flexDirection: "row",
                      gap: 10,
            }}>
          <TouchableOpacity
            style={{
              flexDirection: "row", alignItems: "center", gap: sp(0.8),
              backgroundColor: "rgba(14,165,233,0.12)",
              borderRadius: sp(1.5), paddingVertical: sp(1.2), paddingHorizontal: sp(2),
              borderWidth: 1, borderColor: "rgba(14,165,233,0.28)",
            }}
            onPress={() => setVisible(true)} activeOpacity={0.85}>
            <Text style={{ color: "#0EA5E9", fontSize: fs(19), fontWeight: "500", lineHeight: fs(20) }}>+</Text>
            <Text style={{ color: "#0EA5E9", fontSize: fs(14), fontWeight: "600" }}>Add Person</Text>
        </TouchableOpacity>
        <TouchableOpacity
            style={{
              flexDirection: "row", alignItems: "center", gap: sp(0.8),
              backgroundColor: "rgba(14,165,233,0.12)",
              borderRadius: sp(1.5), paddingVertical: sp(1.2), paddingHorizontal: sp(2),
              borderWidth: 1, borderColor: "rgba(14,165,233,0.28)",
            }}
            onPress={() => setVisibleManual(true)} activeOpacity={0.85}>
            <Text style={{ color: "#0EA5E9", fontSize: fs(14), fontWeight: "600" }}>Manual Search</Text>
          </TouchableOpacity>
              </View>
              </SafeAreaView>
      )}

      {/* ── Result Card ── */}
      {result && (
        <Animated.View style={[resultCardStyle, { opacity: fadeAnim, transform: [{ translateY: resultSlide }] }]}>
          <View style={{
            backgroundColor: "rgba(15,23,40,0.96)",
            borderRadius: sp(2.5),
            borderWidth: 1, borderColor: "rgba(14,165,233,0.2)",
            padding: sp(2.5),
            marginBottom: StatusBar.currentHeight + 5,
            shadowColor: "#0EA5E9", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 20, elevation: 10,
            
          }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: sp(1), marginBottom: sp(1.5) }}>
              <Text style={{ fontSize: fs(11), color: "#475569", fontWeight: "700", textTransform: "uppercase", letterSpacing: 1.2 }}>Scan Result</Text>
            </View>

            <Text style={{ fontSize: fs(22), fontWeight: "800", color: "#F0F9FF", letterSpacing: -0.5, marginBottom: sp(2) }} numberOfLines={2}>
              {result?.department ?? "Please Try Again"}
            </Text>

            {confidencePercent && (
              <>
                <View style={{ flexDirection: "row", backgroundColor: "rgba(8,13,20,0.6)", borderRadius: sp(1.5), padding: sp(1.8) }}>
                  <View style={{ flex: 1 }}>
                    <Text style={{ fontSize: fs(10), color: "#475569", fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.6, marginBottom: 4 }}>Name</Text>
                    <Text style={{ fontSize: fs(14), color: "#F0F9FF", fontWeight: "600" }} numberOfLines={1}>{result?.name ?? "Unknown"}</Text>
                  </View>
                  <View style={{ width: 1, backgroundColor: "rgba(148,163,184,0.15)", marginHorizontal: sp(2) }} />
                  <View style={{ flex: 1 }}>
                    <Text style={{ fontSize: fs(10), color: "#475569", fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.6, marginBottom: 4 }}>Confidence</Text>
                    <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                      <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: confidenceColor }} />
                      <Text style={{ fontSize: fs(14), fontWeight: "700", color: confidenceColor }}>{confidencePercent}</Text>
                    </View>
                  </View>
                </View>
                <TouchableOpacity
                  onPress={() => setVisible(true)} activeOpacity={0.85}
                  style={{ marginTop: sp(1.5), backgroundColor: "rgba(14,165,233,0.12)", borderRadius: sp(1.2), paddingVertical: sp(1.2), alignItems: "center", borderWidth: 1, borderColor: "rgba(14,165,233,0.25)" }}>
                  <Text style={{ color: "#0EA5E9", fontSize: fs(13), fontWeight: "600" }}>Edit Person</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </Animated.View>
      )}

      {/* ── Error / Status banners ── */}
      {error && (
        <View style={[errorBannerStyle, { flexDirection: "row", alignItems: "center", backgroundColor: "rgba(248,113,113,0.12)", borderRadius: sp(2), borderWidth: 1, borderColor: "rgba(248,113,113,0.25)", padding: sp(2), gap: sp(1.5) }]}>
          <View style={{ width: sp(4), height: sp(4), borderRadius: sp(2), backgroundColor: "rgba(248,113,113,0.2)", alignItems: "center", justifyContent: "center" }}>
            <Text style={{ color: "#F87171", fontSize: fs(14), fontWeight: "800" }}>!</Text>
          </View>
          <Text style={{ flex: 1, color: "#FCA5A5", fontSize: fs(13), fontWeight: "500" }}>{error}</Text>
        </View>
      )}

      {statusMsg && !result && !error && (
        <View style={[errorBannerStyle, { flexDirection: "row", alignItems: "center", backgroundColor: "rgba(52,211,153,0.1)", borderRadius: sp(2), borderWidth: 1, borderColor: "rgba(52,211,153,0.25)", padding: sp(2), gap: sp(1.5) }]}>
          <View style={{ width: sp(4), height: sp(4), borderRadius: sp(2), backgroundColor: "rgba(52,211,153,0.15)", alignItems: "center", justifyContent: "center" }}>
            <Text style={{ color: "#34D399", fontSize: fs(14), fontWeight: "800" }}>✓</Text>
          </View>
          <Text style={{ flex: 1, color: "#6EE7B7", fontSize: fs(13), fontWeight: "500" }}>{statusMsg}</Text>
        </View>
      )}

      {/* ── Bottom Controls ── */}
      <SafeAreaView style={{ position: "absolute", bottom: 0, left: 0, right: 0 }}>
        <View style={{
          flexDirection: "row", alignItems: "center", justifyContent: "space-between",
          paddingHorizontal: isTablet ? sp(6) : sp(4),
          paddingTop: sp(2),
          paddingBottom: isLandscape ? sp(1) : sp(2.5),
          gap: sp(1),
        }}>

          {/* Connect / Disconnect */}
          <TouchableOpacity
            style={{ alignItems: "center", gap: sp(0.8), minWidth: sp(9), opacity: wsStatus === "connecting" ? 0.6 : 1 }}
            onPress={isConnected ? disconnectWS : connectWS}
            disabled={wsStatus === "connecting"}
            activeOpacity={0.85}>
            <View style={{
              width: isTablet ? 60 : 52, height: isTablet ? 60 : 52,
              borderRadius: isTablet ? 30 : 26,
              backgroundColor: isConnected ? "rgba(52,211,153,0.12)" : "rgba(148,163,184,0.1)",
              borderWidth: 1, borderColor: isConnected ? "rgba(52,211,153,0.3)" : "rgba(148,163,184,0.2)",
              alignItems: "center", justifyContent: "center",
            }}>
              {wsStatus === "connecting"
                ? <ActivityIndicator color="#FBBF24" size="small" />
                : isConnected
                  ? <View style={{ width: 14, height: 14, borderRadius: 3, backgroundColor: "#34D399" }} />
                  : <View style={{ width: 0, height: 0, borderLeftWidth: 11, borderTopWidth: 7, borderBottomWidth: 7, borderLeftColor: "#94A3B8", borderTopColor: "transparent", borderBottomColor: "transparent", marginLeft: 4 }} />
              }
            </View>
            <Text style={{ color: isConnected ? "#34D399" : "#64748B", fontSize: fs(11), fontWeight: "600" }}>
              {isConnected ? "Disconnect" : "Connect"}
            </Text>
          </TouchableOpacity>

          {/* Scan button — main CTA */}
          <TouchableOpacity
            style={{ alignItems: "center", justifyContent: "center", opacity: isConnected ? 1 : 0.3 }}
            onPress={captureOnce}
            disabled={!isConnected}
            activeOpacity={0.8}>
            <View style={{
              width: scanBtnSize + 16, height: scanBtnSize + 16, borderRadius: (scanBtnSize + 16) / 2,
              backgroundColor: "rgba(14,165,233,0.08)",
              alignItems: "center", justifyContent: "center",
            }}>
              <View style={{
                width: scanBtnSize, height: scanBtnSize, borderRadius: scanBtnSize / 2,
                borderWidth: 3.5, borderColor: scanning ? "#F87171" : "#0EA5E9",
                alignItems: "center", justifyContent: "center",
                backgroundColor: "rgba(14,165,233,0.06)",
              }}>
                <View style={scanning
                  ? { width: scanBtnSize * 0.38, height: scanBtnSize * 0.38, borderRadius: 5, backgroundColor: "#F87171" }
                  : { width: scanBtnSize * 0.64, height: scanBtnSize * 0.64, borderRadius: scanBtnSize * 0.32, backgroundColor: "#0EA5E9" }
                } />
              </View>
            </View>
          </TouchableOpacity>

          {/* Clear */}
          <TouchableOpacity
            style={{ alignItems: "center", gap: sp(0.8), minWidth: sp(9), opacity: (result || error || statusMsg) ? 1 : 0.3 }}
            onPress={() => { setResult(null); setError(null); setStatusMsg(null); setForm({ name: null, department: null, building: null, room: null, school: null }); }}
            disabled={!result && !error && !statusMsg}
            activeOpacity={0.85}>
            <View style={{
              width: isTablet ? 60 : 52, height: isTablet ? 60 : 52,
              borderRadius: isTablet ? 30 : 26,
              backgroundColor: "rgba(148,163,184,0.1)", borderWidth: 1, borderColor: "rgba(148,163,184,0.2)",
              alignItems: "center", justifyContent: "center",
            }}>
              <Text style={{ color: "#94A3B8", fontSize: fs(18), fontWeight: "600" }}>✕</Text>
            </View>
            <Text style={{ color: "#64748B", fontSize: fs(11), fontWeight: "600" }}>Clear</Text>
          </TouchableOpacity>
        </View>

        {/* Back button */}
        {navigation && (
          <TouchableOpacity
            style={{ alignSelf: "center", marginBottom: StatusBar.currentHeight + 5, flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: sp(1), paddingHorizontal: sp(2), borderRadius: sp(1.5), backgroundColor: "rgba(71,85,105,0.4)", borderWidth: 1, borderColor: "rgba(96,165,250,0.25)" }}
            onPress={() => navigation.goBack()} activeOpacity={0.85}>
            <Text style={{ color: "#94A3B8", fontSize: fs(14), fontWeight: "600", letterSpacing: 0.4 }}>← Back</Text>
          </TouchableOpacity>
        )}
      </SafeAreaView>

      {/* ── Add / Edit Person Modal ── */}
      <Modal visible={visible} animationType="slide" transparent statusBarTranslucent>
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.72)", justifyContent: "flex-end" , marginBottom: StatusBar.currentHeight + 5 }}>
          <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ flexGrow: 1, justifyContent: "flex-end" }}>
            <View style={{
              backgroundColor: "#0F1929",
              borderTopLeftRadius: sp(3), borderTopRightRadius: sp(3),
              paddingTop: sp(3), paddingHorizontal: sp(3), paddingBottom: sp(5),
              borderTopWidth: 1, borderColor: "rgba(14,165,233,0.15)",
            }}>
              {/* Handle */}
              <View style={{ width: 38, height: 4, borderRadius: 2, backgroundColor: "rgba(148,163,184,0.25)", alignSelf: "center", marginBottom: sp(2.5) }} />

              <Text style={{ fontSize: fs(22), fontWeight: "800", color: "#F0F9FF", letterSpacing: -0.4, marginBottom: 4 }}>Add / Edit Person</Text>
              <Text style={{ fontSize: fs(14), color: "#475569", marginBottom: sp(3) }}>Enter the person's details below</Text>

              {[
                { label: "Full Name", key: "name", placeholder: "Enter name…" },
                { label: "Department", key: "department", placeholder: "Enter department…" },
              ].map(({ label, key, placeholder }) => (
                <View key={key} style={{ marginBottom: sp(2) }}>
                  <Text style={{ fontSize: fs(11), fontWeight: "700", color: "#64748B", textTransform: "uppercase", letterSpacing: 0.7, marginBottom: sp(0.8) }}>{label}</Text>
                  <TextInput
                    placeholder={placeholder} placeholderTextColor="#334155"
                    value={form?.[key] ?? ""}
                    onChangeText={(t) => setForm({ ...form, [key]: t })}
                    style={{ backgroundColor: "rgba(8,13,20,0.9)", borderRadius: sp(1.5), paddingVertical: sp(1.6), paddingHorizontal: sp(2), fontSize: fs(15), color: "#F0F9FF", borderWidth: 1, borderColor: "rgba(148,163,184,0.15)" }}
                  />
                </View>
              ))}

              {/* Building + Room row */}
              <View style={{ flexDirection: "row", gap: sp(1.5), marginBottom: sp(2) }}>
                {[{ label: "Building", key: "building", placeholder: "Building…" }, { label: "Room", key: "room", placeholder: "Room…" }].map(({ label, key, placeholder }) => (
                  <View key={key} style={{ flex: 1 }}>
                    <Text style={{ fontSize: fs(11), fontWeight: "700", color: "#64748B", textTransform: "uppercase", letterSpacing: 0.7, marginBottom: sp(0.8) }}>{label}</Text>
                    <TextInput
                      placeholder={placeholder} placeholderTextColor="#334155"
                      value={form?.[key] ?? ""}
                      onChangeText={(t) => setForm({ ...form, [key]: t })}
                      style={{ backgroundColor: "rgba(8,13,20,0.9)", borderRadius: sp(1.5), paddingVertical: sp(1.6), paddingHorizontal: sp(2), fontSize: fs(15), color: "#F0F9FF", borderWidth: 1, borderColor: "rgba(148,163,184,0.15)" }}
                    />
                  </View>
                ))}
              </View>

              <View style={{ marginBottom: sp(3) }}>
                <Text style={{ fontSize: fs(11), fontWeight: "700", color: "#64748B", textTransform: "uppercase", letterSpacing: 0.7, marginBottom: sp(0.8) }}>School</Text>
                <TextInput
                  placeholder="Enter school…" placeholderTextColor="#334155"
                  value={form?.school ?? ""}
                  onChangeText={(t) => setForm({ ...form, school: t })}
                  style={{ backgroundColor: "rgba(8,13,20,0.9)", borderRadius: sp(1.5), paddingVertical: sp(1.6), paddingHorizontal: sp(2), fontSize: fs(15), color: "#F0F9FF", borderWidth: 1, borderColor: "rgba(148,163,184,0.15)" }}
                />
              </View>

              <TouchableOpacity
                style={{ backgroundColor: "#0EA5E9", borderRadius: sp(1.8), paddingVertical: sp(2), alignItems: "center", marginBottom: sp(1.5) }}
                onPress={() => { setVisible(false); addPerson(); }} activeOpacity={0.85}>
                <Text style={{ color: "#fff", fontSize: fs(16), fontWeight: "700" }}>Save Person</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={{ borderRadius: sp(1.8), paddingVertical: sp(2), alignItems: "center", borderWidth: 1, borderColor: "rgba(148,163,184,0.18)" }}
                onPress={() => setVisible(false)} activeOpacity={0.85}>
                <Text style={{ color: "#64748B", fontSize: fs(16), fontWeight: "600" }}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
          </Modal>
          
          {/* ── Manually Search Person Modal ── */}
      <Modal visible={visibleManual} animationType="slide" transparent statusBarTranslucent>
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.72)", justifyContent: "flex-end", marginBottom: StatusBar.currentHeight + 5 }}>
          <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ flexGrow: 1, justifyContent: "flex-end" }}>
            <View style={{
              backgroundColor: "#0F1929",
              borderTopLeftRadius: sp(3), borderTopRightRadius: sp(3),
              paddingTop: sp(3), paddingHorizontal: sp(3), paddingBottom: sp(5),
              borderTopWidth: 1, borderColor: "rgba(14,165,233,0.15)",
            }}>
              {/* Handle */}
              <View style={{ width: 38, height: 4, borderRadius: 2, backgroundColor: "rgba(148,163,184,0.25)", alignSelf: "center", marginBottom: sp(2.5) }} />

              <Text style={{ fontSize: fs(22), fontWeight: "800", color: "#F0F9FF", letterSpacing: -0.4, marginBottom: 4 }}>Manual Search</Text>
              <Text style={{ fontSize: fs(14), color: "#475569", marginBottom: sp(3) }}>Enter the person's name below</Text>

              {[
                { label: "Full Name", key: "name", placeholder: "Enter name…" },
              ].map(({ label, key, placeholder }) => (
                <View key={key} style={{ marginBottom: sp(2) }}>
                  <Text style={{ fontSize: fs(11), fontWeight: "700", color: "#64748B", textTransform: "uppercase", letterSpacing: 0.7, marginBottom: sp(0.8) }}>{label}</Text>
                  <TextInput
                    placeholder={placeholder} placeholderTextColor="#334155"
                    value={search}
                    onChangeText={(t) => setSearch( t )}
                    style={{ backgroundColor: "rgba(8,13,20,0.9)", borderRadius: sp(1.5), paddingVertical: sp(1.6), paddingHorizontal: sp(2), fontSize: fs(15), color: "#F0F9FF", borderWidth: 1, borderColor: "rgba(148,163,184,0.15)" }}
                  />
                </View>
              ))}

              <TouchableOpacity
                style={{ backgroundColor: "#0EA5E9", borderRadius: sp(1.8), paddingVertical: sp(2), alignItems: "center", marginBottom: sp(1.5) }}
                onPress={() => { setVisibleManual(false); searchPerson(); }} activeOpacity={0.85}>
                <Text style={{ color: "#fff", fontSize: fs(16), fontWeight: "700" }}>Search</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={{ borderRadius: sp(1.8), paddingVertical: sp(2), alignItems: "center", borderWidth: 1, borderColor: "rgba(148,163,184,0.18)" }}
                onPress={() => setVisibleManual(false)} activeOpacity={0.85}>
                <Text style={{ color: "#64748B", fontSize: fs(16), fontWeight: "600" }}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
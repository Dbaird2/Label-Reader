import { useEffect, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Animated,
  StatusBar,
} from "react-native";

const ACCENT = "#3B82F6";

export default function HomeScreen({ navigation }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;
  const btnScale = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();

    // Soft, looping glow behind the icon
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 2200,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 2200,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, []);

  const handlePressIn = () => {
    Animated.spring(btnScale, {
      toValue: 0.96,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(btnScale, {
      toValue: 1,
      friction: 3,
      useNativeDriver: true,
    }).start();
  };

  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.15, 0.4],
  });

  const glowScale = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.15],
  });

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top corner settings */}
      <TouchableOpacity
        style={styles.settingsBtn}
        onPress={() => navigation.navigate("Settings")}
        accessibilityLabel="Open settings"
        accessibilityRole="button">
        <Text style={styles.settingsIcon}>⚙</Text>
      </TouchableOpacity>

      <Animated.View
        style={[
          styles.content,
          { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
        ]}>
        {/* Icon / logo area */}
        <View style={styles.iconWrap}>
          <Animated.View
            style={[
              styles.iconGlow,
              { opacity: glowOpacity, transform: [{ scale: glowScale }] },
            ]}
          />
          <View style={styles.iconBadge}>
            <Text style={styles.iconGlyph}>◈</Text>
          </View>
        </View>

        {/* Status pill */}
        <View style={styles.pill}>
          <View style={styles.pillDot} />
          <Text style={styles.pillText}>MAILROOM READY</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>
          Label{"\n"}
          <Text style={styles.titleAccent}>Reader</Text>
        </Text>

        {/* Description */}
        <Text style={styles.description}>
          Point your camera at any package label to instantly look up the
          recipient&apos;s campus location. Built for mailroom staff — fast,
          accurate, hands-free.
        </Text>

        {/* Feature highlights */}
        <View style={styles.features}>
          {["Instant lookup", "Hands-free", "On-campus"].map((label) => (
            <View key={label} style={styles.featureItem}>
              <Text style={styles.featureCheck}>✓</Text>
              <Text style={styles.featureText}>{label}</Text>
            </View>
          ))}
        </View>

        {/* Scan button */}
        <Animated.View
          style={[styles.scanBtnWrap, { transform: [{ scale: btnScale }] }]}>
          <TouchableOpacity
            style={styles.scanBtn}
            onPress={() => navigation.navigate("Scanner")}
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            activeOpacity={1}
            accessibilityLabel="Start scanning labels"
            accessibilityRole="button">
            <Text style={styles.scanBtnText}>Scan Labels</Text>
            <View style={styles.scanBtnArrowWrap}>
              <Text style={styles.scanBtnArrow}>→</Text>
            </View>
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>

      {/* Footer */}
      <Text style={styles.footer}>Campus Mail · v1.0</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0A0A0B",
    justifyContent: "center",
  },
  settingsBtn: {
    position: "absolute",
    top: 56,
    right: 24,
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#161618",
    borderWidth: 1,
    borderColor: "#222226",
    zIndex: 10,
  },
  settingsIcon: {
    fontSize: 20,
    color: "#8A8A8F",
  },
  content: {
    paddingHorizontal: 32,
  },
  iconWrap: {
    width: 80,
    height: 80,
    marginBottom: 32,
    alignItems: "center",
    justifyContent: "center",
  },
  iconGlow: {
    position: "absolute",
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: ACCENT,
  },
  iconBadge: {
    width: 72,
    height: 72,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#141416",
    borderWidth: 1,
    borderColor: "#26262B",
  },
  iconGlyph: {
    fontSize: 34,
    color: ACCENT,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: "rgba(59, 130, 246, 0.10)",
    borderWidth: 1,
    borderColor: "rgba(59, 130, 246, 0.25)",
    borderRadius: 999,
    paddingVertical: 6,
    paddingHorizontal: 12,
    marginBottom: 20,
  },
  pillDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: ACCENT,
    marginRight: 8,
  },
  pillText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#93B8F5",
    letterSpacing: 1.2,
  },
  title: {
    fontFamily: "System",
    fontSize: 54,
    fontWeight: "800",
    color: "#F5F5F7",
    lineHeight: 56,
    letterSpacing: -2,
    marginBottom: 20,
  },
  titleAccent: {
    color: ACCENT,
  },
  description: {
    fontSize: 15,
    color: "#9A9AA0",
    lineHeight: 24,
    marginBottom: 28,
    maxWidth: 320,
  },
  features: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginBottom: 44,
  },
  featureItem: {
    flexDirection: "row",
    alignItems: "center",
    marginRight: 18,
    marginBottom: 8,
  },
  featureCheck: {
    fontSize: 12,
    fontWeight: "800",
    color: ACCENT,
    marginRight: 6,
  },
  featureText: {
    fontSize: 13,
    color: "#C2C2C7",
    fontWeight: "500",
  },
  scanBtnWrap: {
    borderRadius: 16,
    shadowColor: ACCENT,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  scanBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: ACCENT,
    borderRadius: 16,
    paddingVertical: 18,
    paddingHorizontal: 24,
  },
  scanBtnText: {
    fontSize: 17,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 0.2,
  },
  scanBtnArrowWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255, 255, 255, 0.20)",
  },
  scanBtnArrow: {
    fontSize: 18,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  footer: {
    position: "absolute",
    bottom: 32,
    alignSelf: "center",
    fontSize: 12,
    color: "#3A3A3F",
    letterSpacing: 1.5,
  },
});

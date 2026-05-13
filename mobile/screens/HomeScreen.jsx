import { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Animated,
  StatusBar,
} from 'react-native';

export default function HomeScreen({ navigation }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;
  const btnScale = useRef(new Animated.Value(1)).current;

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

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top corner settings */}
      <TouchableOpacity
        style={styles.settingsBtn}
        onPress={() => navigation.navigate('Settings')}
        accessibilityLabel="Open settings"
      >
        <Text style={styles.settingsIcon}>⚙</Text>
      </TouchableOpacity>

      <Animated.View
        style={[
          styles.content,
          { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Icon / logo area */}
        <View style={styles.iconWrap}>
          <Text style={styles.iconGlyph}>◈</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>Label{'\n'}Reader</Text>

        {/* Description */}
        <Text style={styles.description}>
          Point your camera at any package label to instantly look up the
          recipient's campus location. Built for mailroom staff — fast,
          accurate, hands-free.
        </Text>

        {/* Scan button */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <TouchableOpacity
            style={styles.scanBtn}
            onPress={() => navigation.navigate('Scanner')}
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            activeOpacity={1}
            accessibilityLabel="Start scanning labels"
            accessibilityRole="button"
          >
            <Text style={styles.scanBtnText}>Scan Labels</Text>
            <Text style={styles.scanBtnArrow}>→</Text>
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
    backgroundColor: '#0D0D0D',
    justifyContent: 'center',
  },
  settingsBtn: {
    position: 'absolute',
    top: 56,
    right: 24,
    padding: 8,
    zIndex: 10,
  },
  settingsIcon: {
    fontSize: 22,
    color: '#555',
  },
  content: {
    paddingHorizontal: 32,
  },
  iconWrap: {
    marginBottom: 28,
  },
  iconGlyph: {
    fontSize: 40,
    color: 'rgba(59, 131, 246, 0.81)',
  },
  title: {
    fontFamily: 'System',
    fontSize: 52,
    fontWeight: '700',
    color: '#F0F0F0',
    lineHeight: 54,
    letterSpacing: -1.5,
    marginBottom: 24,
  },
  description: {
    fontSize: 15,
    color: '#888',
    lineHeight: 24,
    marginBottom: 48,
    maxWidth: 300,
  },
  scanBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: "rgba(59, 131, 246, 0.81)",
    borderRadius: 14,
    paddingVertical: 18,
    paddingHorizontal: 28,
  },
  scanBtnText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: 0.2,
  },
  scanBtnArrow: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
  },
  footer: {
    position: 'absolute',
    bottom: 32,
    alignSelf: 'center',
    fontSize: 12,
    color: '#333',
    letterSpacing: 1,
  },
});
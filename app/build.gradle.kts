plugins {
    id("com.android.application")
}

android {
    namespace = "com.membo.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.membo.app"
        minSdk = 24
        targetSdk = 34
        versionCode = 12
        versionName = "1.0.11"
    }

    // 通过环境变量注入真实 keystore，仓库里不存放任何私钥
    signingConfigs {
        create("release") {
            val ksPath = System.getenv("KEYSTORE_PATH")
            val ksFile = if (ksPath != null) rootProject.file(ksPath) else null
            if (ksFile != null && ksFile.exists()) {
                storeFile = ksFile
                storeType = System.getenv("KEYSTORE_TYPE") ?: "PKCS12"
                storePassword = System.getenv("KEYSTORE_PASSWORD")
                keyAlias = System.getenv("KEY_ALIAS")
                keyPassword = System.getenv("KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
            // 即使是 debug 构建，也不留 WebView 远程调试通道
            isDebuggable = false
        }

        release {
            // 开启代码压缩与资源收缩，包体能压到 1MB 上下，也是安全扫描的加分项
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.webkit:webkit:1.11.0")
}

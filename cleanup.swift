#!/usr/bin/swift
// cleanup.swift — Move photos to Recently Deleted using the native Photos framework.
//
// Usage:
//   1. Run analyze.py first to generate ~/Pictures/uuids_to_delete.txt
//   2. swift ~/Pictures/cleanup.swift
//
// The script reads UUIDs from uuids_to_delete.txt, fetches the corresponding
// PHAssets, and calls PHAssetChangeRequest.deleteAssets(). Photos will show
// a confirmation dialog before deleting. Items land in Recently Deleted (30-day
// recovery window) — nothing is permanently deleted until you empty that album.

import Photos
import Foundation

let uuidFile = (("~/Pictures/uuids_to_delete.txt") as NSString).expandingTildeInPath

guard let contents = try? String(contentsOfFile: uuidFile, encoding: .utf8) else {
    print("❌ Could not read \(uuidFile)")
    print("   Run analyze.py first.")
    exit(1)
}

let uuids = contents
    .components(separatedBy: "\n")
    .map { $0.trimmingCharacters(in: .whitespaces) }
    .filter { !$0.isEmpty }

print("📋 Loaded \(uuids.count) UUIDs")

// Request photo library access
let sema = DispatchSemaphore(value: 0)
var authStatus = PHPhotoLibrary.authorizationStatus(for: .readWrite)

if authStatus == .notDetermined {
    PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
        authStatus = status
        sema.signal()
    }
    sema.wait()
}

guard authStatus == .authorized || authStatus == .limited else {
    print("❌ Photos access denied.")
    print("   Go to System Settings → Privacy & Security → Photos → allow Terminal.")
    exit(1)
}

// Fetch assets by local identifier (matches ZUUID in Photos SQLite database)
print("🔍 Fetching assets...")
let fetchResult = PHAsset.fetchAssets(withLocalIdentifiers: uuids, options: nil)
var assets: [PHAsset] = []
fetchResult.enumerateObjects { asset, _, _ in
    assets.append(asset)
}

let missing = uuids.count - assets.count
print("✅ Found \(assets.count) of \(uuids.count) assets locally")
if missing > 0 {
    print("   (\(missing) are iCloud-only — they'll be trashed once downloaded)")
}

if assets.isEmpty {
    print("⚠️  No local assets found. Try opening Photos.app first, then re-run.")
    exit(0)
}

print("\n🗑️  Moving \(assets.count) photos to Recently Deleted...")
print("   Photos will show a confirmation dialog — click Delete to confirm.\n")

PHPhotoLibrary.shared().performChanges({
    PHAssetChangeRequest.deleteAssets(assets as NSFastEnumeration)
}, completionHandler: { success, error in
    if success {
        print("✅ Done! \(assets.count) photos moved to Recently Deleted.")
        print("   Review: Photos → Albums → Recently Deleted")
        print("   To free space: tap Delete All when you're ready.")
    } else {
        print("❌ Error: \(error?.localizedDescription ?? "unknown error")")
    }
    exit(0)
})

RunLoop.main.run()

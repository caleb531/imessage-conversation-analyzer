#![allow(unexpected_cfgs)]

#[cfg(target_os = "macos")]
use {
    block::ConcreteBlock,
    objc::runtime::{Object, BOOL, YES},
    objc::{class, msg_send, sel, sel_impl},
    std::{
        ffi::{CStr, CString},
        os::raw::c_char,
        ptr,
        sync::{Arc, Condvar, Mutex},
    },
};

use std::path::{Path, PathBuf};

#[cfg(target_os = "macos")]
const CN_ENTITY_TYPE_CONTACTS: i64 = 0;
#[cfg(target_os = "macos")]
const CN_AUTH_STATUS_NOT_DETERMINED: i64 = 0;
#[cfg(target_os = "macos")]
const CN_AUTH_STATUS_AUTHORIZED: i64 = 3;

#[cfg(target_os = "macos")]
#[link(name = "Contacts", kind = "framework")]
extern "C" {}

#[cfg(target_os = "macos")]
#[link(name = "Foundation", kind = "framework")]
extern "C" {}

#[cfg(target_os = "macos")]
struct ObjcOwned(*mut Object);

#[cfg(target_os = "macos")]
impl ObjcOwned {
    #[inline]
    fn as_ptr(&self) -> *mut Object {
        self.0
    }
}

#[cfg(target_os = "macos")]
impl Drop for ObjcOwned {
    fn drop(&mut self) {
        unsafe {
            if !self.0.is_null() {
                let _: () = msg_send![self.0, release];
            }
        }
    }
}

#[tauri::command]
async fn get_contact_names() -> Result<Vec<String>, String> {
    #[cfg(target_os = "macos")]
    {
        tauri::async_runtime::spawn_blocking(move || fetch_contact_names())
            .await
            .map_err(|err| err.to_string())?
    }

    #[cfg(not(target_os = "macos"))]
    {
        Err("Contacts are only available on macOS.".into())
    }
}

#[cfg(target_os = "macos")]
fn fetch_contact_names() -> Result<Vec<String>, String> {
    unsafe {
        let store_ptr: *mut Object = msg_send![class!(CNContactStore), new];
        if store_ptr.is_null() {
            return Err("Failed to create CNContactStore.".into());
        }
        let store = ObjcOwned(store_ptr);
        let store_raw = store.as_ptr();

        ensure_contacts_access(store_raw)?;

        let key_strings = ["givenName", "familyName", "organizationName"];
        let mut c_strings = Vec::with_capacity(key_strings.len());
        let mut ns_keys = Vec::with_capacity(key_strings.len());
        for key in key_strings {
            let c_string = CString::new(key).map_err(|_| format!("Invalid key: {key}"))?;
            let ns_key: *mut Object =
                msg_send![class!(NSString), stringWithUTF8String: c_string.as_ptr()];
            if ns_key.is_null() {
                return Err(format!("Failed to create NSString for {key}."));
            }
            c_strings.push(c_string);
            ns_keys.push(ns_key);
        }

        let keys_array: *mut Object =
            msg_send![class!(NSArray), arrayWithObjects: ns_keys.as_ptr() count: ns_keys.len()];
        if keys_array.is_null() {
            return Err("Failed to create fetch request keys.".into());
        }

        let request_alloc: *mut Object = msg_send![class!(CNContactFetchRequest), alloc];
        if request_alloc.is_null() {
            return Err("Failed to allocate CNContactFetchRequest.".into());
        }
        let request_ptr: *mut Object = msg_send![request_alloc, initWithKeysToFetch: keys_array];
        if request_ptr.is_null() {
            let _: () = msg_send![request_alloc, release];
            return Err("Failed to initialize CNContactFetchRequest.".into());
        }
        let request = ObjcOwned(request_ptr);
        let request_raw = request.as_ptr();

        let contacts = Arc::new(Mutex::new(Vec::<String>::new()));
        let contacts_clone = Arc::clone(&contacts);

        let block = ConcreteBlock::new(move |contact: *mut Object, _stop: *mut BOOL| {
            if let Some(name) = contact_display_name(contact) {
                if let Ok(mut list) = contacts_clone.lock() {
                    if !list.contains(&name) {
                        list.push(name);
                    }
                }
            }
        });
        let block = block.copy();

        let mut error: *mut Object = ptr::null_mut();
        let success: BOOL = msg_send![store_raw,
            enumerateContactsWithFetchRequest: request_raw
            error: &mut error
            usingBlock: &*block
        ];

        if success != YES {
            if !error.is_null() {
                return Err(ns_error_to_string(error));
            } else {
                return Err("Failed to enumerate contacts.".into());
            }
        }

        let mut result = contacts
            .lock()
            .map_err(|_| "Failed to read contacts list.".to_string())?
            .clone();
        result.sort();
        result.dedup();
        Ok(result)
    }
}

#[cfg(target_os = "macos")]
fn ensure_contacts_access(store: *mut Object) -> Result<(), String> {
    unsafe {
        let status: i64 = msg_send![class!(CNContactStore), authorizationStatusForEntityType: CN_ENTITY_TYPE_CONTACTS];
        if status == CN_AUTH_STATUS_AUTHORIZED {
            return Ok(());
        }

        if status != CN_AUTH_STATUS_NOT_DETERMINED {
            return Err("Contacts access is not authorized for this app.".into());
        }

        let state = Arc::new((Mutex::new(None::<(bool, Option<String>)>), Condvar::new()));
        let state_clone = Arc::clone(&state);

        let completion = ConcreteBlock::new(move |granted: BOOL, error: *mut Object| {
            let error_message = if error.is_null() {
                None
            } else {
                Some(ns_error_to_string(error))
            };

            let mut guard = state_clone
                .0
                .lock()
                .expect("poisoned contacts access mutex");
            *guard = Some((granted == YES, error_message));
            state_clone.1.notify_one();
        });
        let completion = completion.copy();

        let _: () = msg_send![store, requestAccessForEntityType: CN_ENTITY_TYPE_CONTACTS completionHandler: &*completion];

        let mut guard = state
            .0
            .lock()
            .map_err(|_| "Failed to request contacts access.".to_string())?;
        while guard.is_none() {
            guard = state
                .1
                .wait(guard)
                .map_err(|_| "Failed while waiting for contacts access.".to_string())?;
        }

        if let Some((granted, error_message)) = guard.take() {
            if granted {
                Ok(())
            } else {
                Err(error_message.unwrap_or_else(|| "Contacts access was not granted.".into()))
            }
        } else {
            Err("Contacts access request returned no result.".into())
        }
    }
}

#[cfg(target_os = "macos")]
unsafe fn contact_display_name(contact: *mut Object) -> Option<String> {
    if contact.is_null() {
        return None;
    }

    let given_ptr: *mut Object = msg_send![contact, givenName];
    let family_ptr: *mut Object = msg_send![contact, familyName];
    let organization_ptr: *mut Object = msg_send![contact, organizationName];

    let given = nsstring_to_string(given_ptr).trim().to_string();
    let family = nsstring_to_string(family_ptr).trim().to_string();
    let organization = nsstring_to_string(organization_ptr).trim().to_string();

    let full_name = match (given.is_empty(), family.is_empty()) {
        (false, false) => format!("{} {}", given, family),
        (false, true) => given,
        (true, false) => family,
        (true, true) => organization,
    };

    let trimmed = full_name.trim().to_string();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed)
    }
}

#[cfg(target_os = "macos")]
unsafe fn nsstring_to_string(ns_string: *mut Object) -> String {
    if ns_string.is_null() {
        return String::new();
    }
    let c_str: *const c_char = msg_send![ns_string, UTF8String];
    if c_str.is_null() {
        String::new()
    } else {
        CStr::from_ptr(c_str).to_string_lossy().into_owned()
    }
}

#[cfg(target_os = "macos")]
unsafe fn ns_error_to_string(error: *mut Object) -> String {
    if error.is_null() {
        return "Unknown contacts error.".into();
    }
    let description: *mut Object = msg_send![error, localizedDescription];
    let message = nsstring_to_string(description);
    if message.trim().is_empty() {
        "Unknown contacts error.".into()
    } else {
        message
    }
}

#[tauri::command]
fn resolve_download_output_path(base_name: String) -> Result<String, String> {
    if base_name.trim().is_empty() {
        return Err("Output filename cannot be empty.".into());
    }

    let base_path = Path::new(&base_name);
    if base_path.is_absolute() || base_path.components().count() > 1 {
        return Err("Output filename must not include directory segments.".into());
    }

    let home_dir = std::env::var("HOME")
        .map(PathBuf::from)
        .map_err(|_| "Could not resolve HOME directory.".to_string())?;
    let downloads_dir = home_dir.join("Downloads");

    let stem = base_path
        .file_stem()
        .and_then(|value| value.to_str())
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| "Output filename is invalid.".to_string())?;

    let extension = base_path
        .extension()
        .and_then(|value| value.to_str())
        .filter(|value| !value.trim().is_empty())
        .unwrap_or("csv");

    let mut index: usize = 0;
    loop {
        let candidate_name = if index == 0 {
            format!("{stem}.{extension}")
        } else {
            format!("{stem}-{index}.{extension}")
        };
        let candidate_path = downloads_dir.join(candidate_name);
        if !candidate_path.exists() {
            return Ok(candidate_path.to_string_lossy().into_owned());
        }
        index += 1;
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_contact_names,
            resolve_download_output_path
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

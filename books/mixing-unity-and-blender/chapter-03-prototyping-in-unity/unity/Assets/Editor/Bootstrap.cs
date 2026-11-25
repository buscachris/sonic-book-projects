using UnityEditor;
using UnityEngine;

namespace SonicBook.Chapter03
{
    public static class Bootstrap
    {
        public static void Check() => Debug.Log("GHZ_PACKAGE_SETUP " + Application.unityVersion);
    }
}

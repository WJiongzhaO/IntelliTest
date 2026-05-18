{
  "root": true,
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": "./tsconfig.json"
  },
  "plugins": ["@typescript-eslint", "react-hooks", "react-refresh"],
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "react-refresh/only-export-components": "warn"
  },
  "ignorePatterns": ["dist", ".eslintrc.cjs", "vite.config.ts"]
}

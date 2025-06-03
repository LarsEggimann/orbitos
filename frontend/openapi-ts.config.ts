import { defaultPlugins } from '@hey-api/openapi-ts'

export default {
  input: './openapi.json',
  output: './src/generated',
  plugins: [
    ...defaultPlugins,
    '@hey-api/client-axios',
    {
      asClass: true,
      name: '@hey-api/sdk',
    },
  ],
}

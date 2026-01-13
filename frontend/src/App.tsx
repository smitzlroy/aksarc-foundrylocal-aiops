import { useState } from 'react'

function App(): JSX.Element {
  const [message] = useState<string>('AKS Arc AI Ops Assistant')

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-dark-50 via-primary-900 to-accent-900">
      <div className="card max-w-2xl">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
          {message}
        </h1>
        <p className="text-dark-600 text-lg">
          Week 1 MVP - Foundation is being built...
        </p>
        <div className="mt-8 p-4 bg-dark-50 rounded-lg border border-primary-500">
          <p className="text-sm text-dark-700">
            🚀 <strong>Status:</strong> Project structure initialized
          </p>
          <p className="text-sm text-dark-700 mt-2">
            🔧 <strong>Next:</strong> Backend API and Kubernetes integration
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
